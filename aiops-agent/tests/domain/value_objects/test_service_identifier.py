"""ServiceIdentifier 值对象测试"""
import pytest

from domain.value_objects.service_identifier import ServiceIdentifier


class TestServiceIdentifier:
    """ServiceIdentifier 测试类"""
    
    def test_create_with_service_name_only(self):
        """测试仅创建服务名"""
        service = ServiceIdentifier(service_name="target-app")
        
        assert service.service_name == "target-app"
        assert service.instance is None
    
    def test_create_with_service_name_and_instance(self):
        """测试创建服务名和实例"""
        service = ServiceIdentifier(
            service_name="target-app",
            instance="192.168.1.10:8080"
        )
        
        assert service.service_name == "target-app"
        assert service.instance == "192.168.1.10:8080"
    
    def test_create_empty_service_name_raises_error(self):
        """测试创建空服务名"""
        with pytest.raises(ValueError, match="服务名不能为空"):
            ServiceIdentifier(service_name="")
    
    def test_create_whitespace_service_name_raises_error(self):
        """测试创建仅空格的服务名"""
        with pytest.raises(ValueError, match="服务名不能为空"):
            ServiceIdentifier(service_name="   ")
    
    def test_is_specific_instance(self):
        """测试判断是否指定实例"""
        generic = ServiceIdentifier(service_name="target-app")
        assert generic.is_specific_instance() is False
        
        specific = ServiceIdentifier(
            service_name="target-app",
            instance="192.168.1.10:8080"
        )
        assert specific.is_specific_instance() is True
        
        empty_instance = ServiceIdentifier(
            service_name="target-app",
            instance=""
        )
        assert empty_instance.is_specific_instance() is False
    
    def test_to_dict(self):
        """测试转换为字典"""
        service = ServiceIdentifier(
            service_name="target-app",
            instance="192.168.1.10:8080"
        )
        
        data = service.to_dict()
        assert data["service_name"] == "target-app"
        assert data["instance"] == "192.168.1.10:8080"
    
    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "service_name": "target-app",
            "instance": "192.168.1.10:8080"
        }
        
        service = ServiceIdentifier.from_dict(data)
        assert service.service_name == "target-app"
        assert service.instance == "192.168.1.10:8080"
    
    def test_from_dict_without_instance(self):
        """测试从字典创建（无实例）"""
        data = {
            "service_name": "target-app"
        }
        
        service = ServiceIdentifier.from_dict(data)
        assert service.service_name == "target-app"
        assert service.instance is None
    
    def test_immutable(self):
        """测试不可变性"""
        service = ServiceIdentifier(service_name="target-app")
        
        with pytest.raises(AttributeError):
            service.service_name = "new-app"  # type: ignore
    
    def test_equality(self):
        """测试值相等性"""
        s1 = ServiceIdentifier(
            service_name="target-app",
            instance="192.168.1.10:8080"
        )
        s2 = ServiceIdentifier(
            service_name="target-app",
            instance="192.168.1.10:8080"
        )
        
        assert s1 == s2
        assert hash(s1) == hash(s2)
    
    def test_string_representation_with_instance(self):
        """测试字符串表示（有实例）"""
        service = ServiceIdentifier(
            service_name="target-app",
            instance="192.168.1.10:8080"
        )
        
        assert str(service) == "target-app@192.168.1.10:8080"
    
    def test_string_representation_without_instance(self):
        """测试字符串表示（无实例）"""
        service = ServiceIdentifier(service_name="target-app")
        
        assert str(service) == "target-app"
