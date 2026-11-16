"""TimeRange 值对象测试"""
import pytest
from datetime import datetime, timedelta

from domain.value_objects.time_range import TimeRange


class TestTimeRange:
    """TimeRange 测试类"""
    
    def test_create_valid_time_range(self):
        """测试创建有效的时间范围"""
        start = datetime(2026, 11, 16, 10, 0, 0)
        end = datetime(2026, 11, 16, 10, 5, 0)
        
        time_range = TimeRange(start=start, end=end)
        
        assert time_range.start == start
        assert time_range.end == end
    
    def test_create_invalid_time_range_raises_error(self):
        """测试创建无效时间范围（开始时间晚于结束时间）"""
        start = datetime(2026, 11, 16, 10, 5, 0)
        end = datetime(2026, 11, 16, 10, 0, 0)
        
        with pytest.raises(ValueError, match="时间范围无效"):
            TimeRange(start=start, end=end)
    
    def test_create_equal_time_range_raises_error(self):
        """测试创建相等时间范围（开始时间等于结束时间）"""
        timestamp = datetime(2026, 11, 16, 10, 0, 0)
        
        with pytest.raises(ValueError, match="时间范围无效"):
            TimeRange(start=timestamp, end=timestamp)
    
    def test_duration_seconds(self):
        """测试计算时长"""
        start = datetime(2026, 11, 16, 10, 0, 0)
        end = datetime(2026, 11, 16, 10, 5, 30)  # 5分30秒
        
        time_range = TimeRange(start=start, end=end)
        
        assert time_range.duration_seconds() == 330.0
    
    def test_contains(self):
        """测试判断时间点是否在范围内"""
        start = datetime(2026, 11, 16, 10, 0, 0)
        end = datetime(2026, 11, 16, 10, 5, 0)
        time_range = TimeRange(start=start, end=end)
        
        # 边界值
        assert time_range.contains(start) is True
        assert time_range.contains(end) is True
        
        # 范围内
        assert time_range.contains(datetime(2026, 11, 16, 10, 2, 30)) is True
        
        # 范围外
        assert time_range.contains(datetime(2026, 11, 16, 9, 59, 59)) is False
        assert time_range.contains(datetime(2026, 11, 16, 10, 5, 1)) is False
    
    def test_overlaps(self):
        """测试判断是否重叠"""
        range1 = TimeRange(
            start=datetime(2026, 11, 16, 10, 0, 0),
            end=datetime(2026, 11, 16, 10, 5, 0)
        )
        
        # 重叠（部分）
        range2 = TimeRange(
            start=datetime(2026, 11, 16, 10, 3, 0),
            end=datetime(2026, 11, 16, 10, 7, 0)
        )
        assert range1.overlaps(range2) is True
        assert range2.overlaps(range1) is True
        
        # 包含
        range3 = TimeRange(
            start=datetime(2026, 11, 16, 10, 1, 0),
            end=datetime(2026, 11, 16, 10, 4, 0)
        )
        assert range1.overlaps(range3) is True
        
        # 不重叠
        range4 = TimeRange(
            start=datetime(2026, 11, 16, 10, 6, 0),
            end=datetime(2026, 11, 16, 10, 8, 0)
        )
        assert range1.overlaps(range4) is False
        
        # 边界不重叠（开始时间等于结束时间）
        range5 = TimeRange(
            start=datetime(2026, 11, 16, 10, 5, 0),
            end=datetime(2026, 11, 16, 10, 7, 0)
        )
        assert range1.overlaps(range5) is False
    
    def test_to_dict(self):
        """测试转换为字典"""
        start = datetime(2026, 11, 16, 10, 0, 0)
        end = datetime(2026, 11, 16, 10, 5, 0)
        time_range = TimeRange(start=start, end=end)
        
        data = time_range.to_dict()
        
        assert data["start"] == "2026-11-16T10:00:00"
        assert data["end"] == "2026-11-16T10:05:00"
    
    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "start": "2026-11-16T10:00:00",
            "end": "2026-11-16T10:05:00"
        }
        
        time_range = TimeRange.from_dict(data)
        
        assert time_range.start == datetime(2026, 11, 16, 10, 0, 0)
        assert time_range.end == datetime(2026, 11, 16, 10, 5, 0)
    
    def test_immutable(self):
        """测试不可变性"""
        start = datetime(2026, 11, 16, 10, 0, 0)
        end = datetime(2026, 11, 16, 10, 5, 0)
        time_range = TimeRange(start=start, end=end)
        
        with pytest.raises(AttributeError):
            time_range.start = datetime(2026, 11, 16, 10, 1, 0)  # type: ignore
    
    def test_equality(self):
        """测试值相等性"""
        start = datetime(2026, 11, 16, 10, 0, 0)
        end = datetime(2026, 11, 16, 10, 5, 0)
        
        range1 = TimeRange(start=start, end=end)
        range2 = TimeRange(start=start, end=end)
        
        assert range1 == range2
        assert hash(range1) == hash(range2)
