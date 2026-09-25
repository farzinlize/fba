from pydantic import Field

from backend.common.schema import SchemaBase


class CpuInfo(SchemaBase):
    """CPU information"""

    physical_num: int = Field(description='Physical core count')
    logical_num: int = Field(description='Logical core count')
    max_freq: float = Field(description='Maximum frequency (MHz)')
    min_freq: float = Field(description='Minimum frequency (MHz)')
    current_freq: float = Field(description='Current frequency (MHz)')
    usage: float = Field(description='Usage (%)')


class MemInfo(SchemaBase):
    """Memory information"""

    total: float = Field(description='Total capacity (GB)')
    used: float = Field(description='Used (GB)')
    free: float = Field(description='Available (GB)')
    usage: float = Field(description='Usage (%)')


class SysInfo(SchemaBase):
    """System information"""

    name: str = Field(description='Hostname')
    os: str = Field(description='Operating system')
    ip: str = Field(description='IP address')
    arch: str = Field(description='System architecture')


class DiskInfo(SchemaBase):
    """Disk information"""

    dir: str = Field(description='Mount point')
    device: str = Field(description='Device name')
    type: str = Field(description='Filesystem type')
    total: str = Field(description='Total capacity')
    used: str = Field(description='Used')
    free: str = Field(description='Available')
    usage: str = Field(description='Usage (%)')


class ServiceInfo(SchemaBase):
    """Service process information"""

    name: str = Field(description='Service name')
    version: str = Field(description='Version')
    home: str = Field(description='Installation path')
    startup: str = Field(description='Start time')
    elapsed: str = Field(description='Uptime')
    cpu_usage: str = Field(description='CPU usage')
    mem_vms: str = Field(description='Virtual memory')
    mem_rss: str = Field(description='Physical memory')
    mem_free: str = Field(description='Available memory')


class ServerMonitorInfo(SchemaBase):
    """Server monitoring information"""

    cpu: CpuInfo = Field(description='CPU information')
    mem: MemInfo = Field(description='Memory information')
    sys: SysInfo = Field(description='System information')
    disk: list[DiskInfo] = Field(description='Disk information')
    service: ServiceInfo = Field(description='Service information')


class RedisServerInfo(SchemaBase):
    """Redis server information"""

    redis_version: str = Field(description='Version number')
    redis_mode: str = Field(description='Run mode')
    role: str = Field(description='Node role')
    tcp_port: str = Field(description='Listening port')
    uptime: str = Field(description='Uptime')
    connected_clients: str = Field(description='Connected clients')
    blocked_clients: str = Field(description='Blocked clients')
    used_memory_human: str = Field(description='Used memory')
    used_memory_rss_human: str = Field(description='RSS memory')
    maxmemory_human: str = Field(description='Maximum memory limit')
    mem_fragmentation_ratio: str = Field(description='Memory fragmentation ratio')
    instantaneous_ops_per_sec: str = Field(description='Operations per second')
    total_commands_processed: str = Field(description='Total commands processed')
    rejected_connections: str = Field(description='Rejected connections')
    keys_num: str = Field(description='Total keys')


class RedisCommandStat(SchemaBase):
    """Redis command statistics"""

    name: str = Field(description='Command name')
    value: str = Field(description='Call count')


class RedisMonitorInfo(SchemaBase):
    """Redis monitoring information"""

    info: RedisServerInfo = Field(description='Server information')
    stats: list[RedisCommandStat] = Field(description='Command statistics')
