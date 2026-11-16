"""Prometheus 指标定义"""
from prometheus_client import Counter, Histogram, Gauge, Info

# ====================
# 诊断相关指标
# ====================

diagnosis_total = Counter(
    'diagnosis_total',
    'Total number of diagnoses',
    ['service_name', 'status']
)

diagnosis_duration_seconds = Histogram(
    'diagnosis_duration_seconds',
    'Diagnosis duration in seconds',
    ['service_name'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600]
)

diagnosis_in_progress = Gauge(
    'diagnosis_in_progress',
    'Number of diagnoses currently in progress',
    ['service_name']
)

diagnosis_stage_duration_seconds = Histogram(
    'diagnosis_stage_duration_seconds',
    'Duration of each diagnosis stage in seconds',
    ['service_name', 'stage'],
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

# ====================
# 外部调用指标
# ====================

external_call_total = Counter(
    'external_call_total',
    'Total number of external calls',
    ['target', 'method', 'status']
)

external_call_duration_seconds = Histogram(
    'external_call_duration_seconds',
    'External call duration in seconds',
    ['target', 'method'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10, 30]
)

external_call_errors_total = Counter(
    'external_call_errors_total',
    'Total number of external call errors',
    ['target', 'method', 'error_type']
)

# ====================
# 缓存指标
# ====================

cache_hit_total = Counter(
    'cache_hit_total',
    'Total number of cache hits',
    ['cache_type', 'operation']
)

cache_miss_total = Counter(
    'cache_miss_total',
    'Total number of cache misses',
    ['cache_type', 'operation']
)

cache_operation_duration_seconds = Histogram(
    'cache_operation_duration_seconds',
    'Cache operation duration in seconds',
    ['cache_type', 'operation'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1]
)

# ====================
# 数据库指标
# ====================

database_query_total = Counter(
    'database_query_total',
    'Total number of database queries',
    ['operation', 'table', 'status']
)

database_query_duration_seconds = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5]
)

database_connection_pool_size = Gauge(
    'database_connection_pool_size',
    'Current size of database connection pool'
)

database_connection_pool_available = Gauge(
    'database_connection_pool_available',
    'Number of available connections in pool'
)

# ====================
# 证据和根因指标
# ====================

evidence_collected_total = Counter(
    'evidence_collected_total',
    'Total number of evidences collected',
    ['service_name', 'evidence_type']
)

root_cause_identified_total = Counter(
    'root_cause_identified_total',
    'Total number of root causes identified',
    ['service_name', 'problem_type']
)

root_cause_confidence = Histogram(
    'root_cause_confidence',
    'Confidence of identified root causes',
    ['service_name', 'problem_type'],
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

# ====================
# 消息队列指标
# ====================

message_published_total = Counter(
    'message_published_total',
    'Total number of messages published',
    ['topic', 'event_type', 'status']
)

message_publish_duration_seconds = Histogram(
    'message_publish_duration_seconds',
    'Message publish duration in seconds',
    ['topic', 'event_type'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5]
)

# ====================
# 应用信息
# ====================

app_info = Info('app_info', 'Application information')

# 设置应用信息（在应用启动时调用）
def set_app_info(name: str, version: str, environment: str):
    """设置应用信息
    
    Args:
        name: 应用名称
        version: 应用版本
        environment: 运行环境
    """
    app_info.info({
        'name': name,
        'version': version,
        'environment': environment
    })
