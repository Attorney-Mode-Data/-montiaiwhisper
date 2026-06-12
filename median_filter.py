import torch
import torch.nn.functional as F

def median_filter(x: torch.Tensor, filter_width: int):
    """
    Apply a median filter of width `filter_width` along the last dimension of `x`.
    Works on CPU and CUDA (if available). No external dependencies.
    """
    # Validate filter width
    if filter_width <= 0 or filter_width % 2 == 0:
        raise ValueError("filter_width must be a positive odd integer")
    
    pad_width = filter_width // 2
    n = x.shape[-1]
    
    # If input is too short, return as is
    if n <= pad_width:
        return x.clone()
    
    # Pad with reflect mode
    x_pad = F.pad(x, (pad_width, pad_width), mode="reflect")
    
    # Use unfold to create sliding windows
    # unfold(dimension, size, step) -> (..., L, filter_width)
    unfolded = x_pad.unfold(dimension=-1, size=filter_width, step=1)
    
    # Compute median along the last dimension (filter_width)
    # Note: torch.median is slower on CPU but reliable
    median = unfolded.median(dim=-1).values
    
    return median
