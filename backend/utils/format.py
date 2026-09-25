def fmt_seconds(seconds: int) -> str:
    """Format seconds as a readable duration string"""
    days, rem = divmod(int(seconds), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f'{days} days')
    if hours:
        parts.append(f'{hours} hours')
    if minutes:
        parts.append(f'{minutes} minutes')
    return ' '.join(parts) if parts else '0 seconds'


def fmt_bytes(size: float) -> str:
    s, factor = size, 1024
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(s) < factor:
            return f'{s:.2f} {unit}B'
        s /= factor
    return f'{s:.2f} YB'
