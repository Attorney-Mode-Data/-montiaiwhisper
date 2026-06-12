import functools
import warnings
from typing import Optional, Tuple

import numpy as np
import torch

try:
    import triton
    import triton.language as tl

    TRITON_AVAILABLE = torch.cuda.is_available()
    if not TRITON_AVAILABLE:
        warnings.warn("CUDA not available; Triton kernels disabled, using PyTorch fallback.")
except ImportError:
    TRITON_AVAILABLE = False
    warnings.warn("triton not installed; using PyTorch fallback.")


# ----------------------------------------------------------------------
# Triton kernels (only used if CUDA available)
# ----------------------------------------------------------------------
if TRITON_AVAILABLE:

    @triton.jit
    def dtw_kernel(
        cost, trace, x, x_stride, cost_stride, trace_stride, N, M, BLOCK_SIZE: tl.constexpr
    ):
        """Triton DTW kernel – computes cumulative cost and traceback."""
        offsets = tl.arange(0, BLOCK_SIZE)
        mask = offsets < M

        # Iterate over anti‑diagonals
        for k in range(1, N + M + 1):
            # Load three previous cost values
            p0 = cost + (k - 1) * cost_stride
            p1 = cost + k * cost_stride
            p2 = cost + k * cost_stride + 1

            c0 = tl.load(p0 + offsets, mask=mask, other=float("inf"))
            c1 = tl.load(p1 + offsets, mask=mask, other=float("inf"))
            c2 = tl.load(p2 + offsets, mask=mask, other=float("inf"))

            # Current row of the distance matrix
            x_row = tl.load(x + (k - 1) * x_stride + offsets, mask=mask, other=0.0)

            # DTW recurrence: cost = x_row + min(c0, c1, c2)
            min_prev = tl.minimum(tl.minimum(c0, c1), c2)
            cost_row = x_row + min_prev

            # Write new cost
            cost_ptr = cost + (k + 1) * cost_stride + 1
            tl.store(cost_ptr + offsets, cost_row, mask=mask)

            # Write traceback directions (0=diag, 1=up, 2=left)
            trace_ptr = trace + (k + 1) * trace_stride + 1
            # Use tl.where with integer masks
            is_diag = (c2 <= c0) & (c2 <= c1)
            is_up = (c1 <= c0) & (c1 <= c2)
            # Default to left if neither (should not happen)
            tl.store(trace_ptr + offsets, 2, mask=mask & is_diag)
            tl.store(trace_ptr + offsets, 1, mask=mask & is_up)
            tl.store(trace_ptr + offsets, 0, mask=mask & ~is_diag & ~is_up)

    @functools.lru_cache(maxsize=None)
    def median_kernel(filter_width: int):
        """Generate a Triton kernel for median filtering of given width."""
        # Template for the kernel
        @triton.jit
        def kernel(y, x, x_stride, y_stride, BLOCK_SIZE: tl.constexpr):
            row_idx = tl.program_id(0)
            offsets = tl.arange(0, BLOCK_SIZE)
            mask = offsets < y_stride

            x_ptr = x + row_idx * x_stride
            y_ptr = y + row_idx * y_stride

            # Placeholders – will be replaced with actual code
            LOAD_ALL_ROWS_HERE
            BUBBLESORT_HERE
            tl.store(y_ptr + offsets, MIDDLE_ROW_HERE, mask=mask)

        # Build dynamic source: load `filter_width` rows
        load_lines = [
            f"    row{i} = tl.load(x_ptr + offsets + {i}, mask=mask, other=0.0)"
            for i in range(filter_width)
        ]
        new_src = kernel.src.replace("    LOAD_ALL_ROWS_HERE", "\n".join(load_lines))

        # Build bubble sort for `filter_width` elements
        sort_steps = []
        for i in range(filter_width // 2 + 1):  # enough passes to get median to middle
            for j in range(filter_width - i - 1):
                sort_steps.append(
                    f"    smaller = tl.where(row{j} < row{j + 1}, row{j}, row{j + 1})\n"
                    f"    larger = tl.where(row{j} > row{j + 1}, row{j}, row{j + 1})\n"
                    f"    row{j} = smaller\n"
                    f"    row{j + 1} = larger"
                )
        sort_code = "\n\n".join(sort_steps)
        new_src = new_src.replace("    BUBBLESORT_HERE", sort_code)

        # Replace median placeholder
        median_idx = filter_width // 2
        new_src = new_src.replace("MIDDLE_ROW_HERE", f"row{median_idx}")

        # Create new JIT function with updated source
        kernel = triton.JITFunction(kernel.fn)
        if hasattr(kernel, "_unsafe_update_src"):
            kernel._unsafe_update_src(new_src)
            kernel.hash = None
        else:
            kernel.src = new_src
        return kernel

    def median_filter_cuda(x: torch.Tensor, filter_width: int) -> torch.Tensor:
        """Apply median filter using Triton (CUDA only)."""
        if not x.is_cuda:
            raise RuntimeError("median_filter_cuda requires CUDA tensor")
        slices = x.contiguous().unfold(-1, filter_width, 1)
        grid = np.prod(slices.shape[:-2])
        kernel = median_kernel(filter_width)
        y = torch.empty_like(slices[..., 0])
        BLOCK_SIZE = 1 << (y.stride(-2) - 1).bit_length()
        kernel[(grid,)](
            y, x,
            x.stride(-2),
            y.stride(-2),
            BLOCK_SIZE=BLOCK_SIZE,
        )
        return y

# ----------------------------------------------------------------------
# PyTorch fallbacks (CPU or when Triton not available)
# ----------------------------------------------------------------------
def median_filter_cpu(x: torch.Tensor, filter_width: int) -> torch.Tensor:
    """Median filter using PyTorch's unfold + median (works on CPU/CUDA)."""
    # unfold: (..., L, filter_width)
    unfolded = x.unfold(dimension=-1, size=filter_width, step=1)
    # median along the last dimension
    median = unfolded.median(dim=-1).values
    return median


def dtw_cpu(x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Dynamic Time Warping using PyTorch (no Triton).
    Args:
        x: distance matrix of shape (N, M)
    Returns:
        cost: cumulative cost matrix (N+1, M+1)
        trace: traceback matrix (N+1, M+1)
    """
    N, M = x.shape
    cost = torch.full((N + 1, M + 1), float("inf"), device=x.device, dtype=x.dtype)
    trace = torch.zeros((N + 1, M + 1), dtype=torch.int8, device=x.device)
    cost[0, 0] = 0.0

    for i in range(1, N + 1):
        for j in range(1, M + 1):
            c0 = cost[i - 1, j - 1]  # diag
            c1 = cost[i - 1, j]      # up
            c2 = cost[i, j - 1]      # left
            min_val, idx = torch.min(torch.stack([c0, c1, c2]), dim=0)
            cost[i, j] = x[i - 1, j - 1] + min_val
            trace[i, j] = idx.item()  # 0=diag,1=up,2=left
    return cost, trace


# ----------------------------------------------------------------------
# Unified dispatch functions
# ----------------------------------------------------------------------
def median_filter(x: torch.Tensor, filter_width: int) -> torch.Tensor:
    """
    Apply median filter along last dimension. Uses Triton if available and input is CUDA,
    otherwise falls back to PyTorch implementation.
    """
    if x.is_cuda and TRITON_AVAILABLE and filter_width > 2:
        # Triton median filter can be faster, but only for certain widths
        return median_filter_cuda(x, filter_width)
    else:
        return median_filter_cpu(x, filter_width)


def dtw(x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Compute DTW cost and traceback matrices. Uses Triton kernel if CUDA available and
    input is on GPU; otherwise uses PyTorch loops (CPU or fallback).
    """
    if x.is_cuda and TRITON_AVAILABLE:
        N, M = x.shape
        # Ensure contiguous and 2D
        x_contig = x.contiguous()
        # Allocate cost and trace
        cost = torch.full((N + 1, M + 1), float("inf"), device=x.device, dtype=x.dtype)
        trace = torch.zeros((N + 1, M + 1), dtype=torch.int8, device=x.device)
        # Initialize first row/col (not needed as inf, but first element 0)
        cost[0, 0] = 0.0
        # Choose block size
        BLOCK_SIZE = 32  # tune
        grid = ( (M + BLOCK_SIZE - 1) // BLOCK_SIZE, )
        dtw_kernel[grid](
            cost, trace, x_contig,
            x_contig.stride(-2),
            cost.stride(-2),
            trace.stride(-2),
            N, M,
            BLOCK_SIZE=BLOCK_SIZE,
        )
        return cost, trace
    else:
        return dtw_cpu(x)
