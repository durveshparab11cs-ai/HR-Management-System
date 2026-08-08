"""
app/repositories/hospital_repository.py
========================================
Data access layer for Hospital operations
"""

from typing import List, Optional
from sqlalchemy import or_

from app.extensions.database import db
from app.models.hospital import Hospital


class HospitalRepository:
    """Repository for Hospital CRUD operations."""
    
    def get_all(self, include_inactive: bool = False) -> List[Hospital]:
        """
        Get all hospitals.
        
        Args:
            include_inactive: If True, include inactive hospitals
            
        Returns:
            List of Hospital objects
        """
        query = Hospital.query.filter_by(is_deleted=False)
        
        if not include_inactive:
            query = query.filter_by(is_active=True)
        
        return query.order_by(Hospital.hospital_name).all()
    
    def get_by_id(self, hospital_id: int) -> Optional[Hospital]:
        """Get hospital by ID."""
        return Hospital.query.filter_by(id=hospital_id, is_deleted=False).first()
    
    def get_by_code(self, hospital_code: str) -> Optional[Hospital]:
        """Get hospital by code."""
        return Hospital.query.filter_by(
            hospital_code=hospital_code, 
            is_deleted=False
        ).first()
    
    def get_by_name(self, hospital_name: str) -> Optional[Hospital]:
        """Get hospital by exact name."""
        return Hospital.query.filter_by(
            hospital_name=hospital_name,
            is_deleted=False
        ).first()
    
    def search(self, query: str) -> List[Hospital]:
        """
        Search hospitals by name or code.
        
        Args:
            query: Search string
            
        Returns:
            List of matching hospitals
        """
        search_pattern = f"%{query}%"
        return Hospital.query.filter(
            Hospital.is_deleted == False,
            or_(
                Hospital.hospital_name.ilike(search_pattern),
                Hospital.hospital_code.ilike(search_pattern),
                Hospital.location.ilike(search_pattern),
                Hospital.city.ilike(search_pattern)
            )
        ).order_by(Hospital.hospital_name).all()
    
    def create(
        self,
        hospital_name: str,
        latitude: float,
        longitude: float,
        hospital_code: str = None,
        location: str = None,
        address: str = None,
        city: str = None,
        state: str = None,
        allowed_radius_metres: int = 100,
        is_active: bool = True,
        status: str = "Active"
    ) -> Hospital:
        """
        Create a new hospital.
        
        Args:
            hospital_name: Hospital name
            latitude: GPS latitude
            longitude: GPS longitude
            hospital_code: Optional hospital code
            location: Optional location name
            address: Optional full address
            city: Optional city
            state: Optional state
            allowed_radius_metres: GPS radius in metres (default: 100)
            is_active: Active status (default: True)
            status: Status string (default: "Active")
            
        Returns:
            Created Hospital object
        """
        hospital = Hospital(
            hospital_name=hospital_name,
            hospital_code=hospital_code,
            latitude=latitude,
            longitude=longitude,
            location=location,
            address=address,
            city=city,
            state=state,
            allowed_radius_metres=allowed_radius_metres,
            is_active=is_active,
            status=status
        )
        
        db.session.add(hospital)
        db.session.flush()  # Get ID without committing
        
        return hospital
    
    def update(
        self,
        hospital_id: int,
        **kwargs
    ) -> Optional[Hospital]:
        """
        Update hospital details.
        
        Args:
            hospital_id: Hospital ID
            **kwargs: Fields to update
            
        Returns:
            Updated Hospital object or None if not found
        """
        hospital = self.get_by_id(hospital_id)
        if not hospital:
            return None
        
        # Update allowed fields
        allowed_fields = [
            'hospital_name', 'hospital_code', 'latitude', 'longitude',
            'location', 'address', 'city', 'state',
            'allowed_radius_metres', 'is_active', 'status'
        ]
        
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(hospital, key, value)
        
        db.session.flush()
        return hospital
    
    def delete(self, hospital_id: int) -> bool:
        """
        Soft delete a hospital.
        
        Args:
            hospital_id: Hospital ID
            
        Returns:
            True if deleted, False if not found
        """
        hospital = self.get_by_id(hospital_id)
        if not hospital:
            return False
        
        hospital.is_deleted = True
        db.session.flush()
        return True
    
    def check_duplicate(self, hospital_name: str, hospital_code: str = None, exclude_id: int = None) -> bool:
        """
        Check if hospital with same name or code already exists.
        
        Args:
            hospital_name: Hospital name to check
            hospital_code: Hospital code to check (optional)
            exclude_id: Hospital ID to exclude (for updates)
            
        Returns:
            True if duplicate exists
        """
        query = Hospital.query.filter_by(is_deleted=False)
        
        if exclude_id:
            query = query.filter(Hospital.id != exclude_id)
        
        # Check name if provided and not empty
        if hospital_name and hospital_name.strip():
            if query.filter(Hospital.hospital_name.ilike(hospital_name.strip())).first():
                return True
        
        # Check code if provided and not empty
        if hospital_code and hospital_code.strip():
            if query.filter(Hospital.hospital_code == hospital_code.strip()).first():
                return True
        
        return False
    
    def get_active_count(self) -> int:
        """Get count of active hospitals."""
        return Hospital.query.filter_by(is_deleted=False, is_active=True).count()
    
    def get_by_location(self, city: str = None, state: str = None) -> List[Hospital]:
        """
        Get hospitals by location.
        
        Args:
            city: City name
            state: State name
            
        Returns:
            List of hospitals
        """
        query = Hospital.query.filter_by(is_deleted=False, is_active=True)
        
        if city:
            query = query.filter(Hospital.city.ilike(f"%{city}%"))
        
        if state:
            query = query.filter(Hospital.state.ilike(f"%{state}%"))
        
        return query.order_by(Hospital.hospital_name).all()
