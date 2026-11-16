"""Confidence 值对象测试"""
import pytest

from domain.value_objects.confidence import Confidence


class TestConfidence:
    """Confidence 测试类"""
    
    def test_create_valid_confidence(self):
        """测试创建有效置信度"""
        confidence = Confidence(0.75)
        assert confidence.value == 0.75
    
    def test_create_zero_confidence(self):
        """测试创建 0.0 置信度"""
        confidence = Confidence(0.0)
        assert confidence.value == 0.0
    
    def test_create_one_confidence(self):
        """测试创建 1.0 置信度"""
        confidence = Confidence(1.0)
        assert confidence.value == 1.0
    
    def test_create_negative_confidence_raises_error(self):
        """测试创建负数置信度"""
        with pytest.raises(ValueError, match="置信度必须在 0.0 ~ 1.0 之间"):
            Confidence(-0.1)
    
    def test_create_greater_than_one_confidence_raises_error(self):
        """测试创建大于 1.0 的置信度"""
        with pytest.raises(ValueError, match="置信度必须在 0.0 ~ 1.0 之间"):
            Confidence(1.1)
    
    def test_is_high(self):
        """测试判断高置信度"""
        high = Confidence(0.8)
        assert high.is_high() is True
        assert high.is_high(threshold=0.9) is False
        
        low = Confidence(0.5)
        assert low.is_high() is False
    
    def test_is_low(self):
        """测试判断低置信度"""
        low = Confidence(0.2)
        assert low.is_low() is True
        assert low.is_low(threshold=0.1) is False
        
        high = Confidence(0.5)
        assert high.is_low() is False
    
    def test_percentage(self):
        """测试转换为百分比"""
        confidence = Confidence(0.75)
        assert confidence.percentage() == 75.0
        
        zero = Confidence(0.0)
        assert zero.percentage() == 0.0
    
    def test_comparison(self):
        """测试比较操作"""
        c1 = Confidence(0.5)
        c2 = Confidence(0.7)
        c3 = Confidence(0.5)
        
        assert c1 < c2
        assert c2 > c1
        assert c1 <= c2
        assert c1 <= c3
        assert c2 >= c1
        assert c1 >= c3
    
    def test_immutable(self):
        """测试不可变性"""
        confidence = Confidence(0.75)
        with pytest.raises(AttributeError):
            confidence.value = 0.8  # type: ignore
    
    def test_equality(self):
        """测试值相等性"""
        c1 = Confidence(0.75)
        c2 = Confidence(0.75)
        
        assert c1 == c2
        assert hash(c1) == hash(c2)
    
    def test_string_representation(self):
        """测试字符串表示"""
        confidence = Confidence(0.756)
        assert str(confidence) == "75.6%"
