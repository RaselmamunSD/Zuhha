from rest_framework import serializers
from .models import Country, City


class CountrySerializer(serializers.ModelSerializer):
    cities_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Country
        fields = ['id', 'name', 'code', 'phone_code', 'currency', 'currency_symbol', 'is_active', 'cities_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_cities_count(self, obj):
        return obj.cities.count()


class CitySerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source='country.name', read_only=True)
    country_code = serializers.CharField(source='country.code', read_only=True)
    
    class Meta:
        model = City
        fields = [
            'id', 'name', 'country', 'country_name', 'country_code',
            'latitude', 'longitude', 'timezone', 'elevation',
            'is_active', 'is_capital', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class CityListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views."""
    country_name = serializers.CharField(source='country.name', read_only=True)
    
    class Meta:
        model = City
        fields = ['id', 'name', 'country_name', 'timezone', 'is_capital']

