-- Update Head office GPS allowed radius to 150 meters
UPDATE hospitals 
SET allowed_radius_metres = 150 
WHERE hospital_name = 'Head office';

-- Verify update
SELECT id, hospital_name, latitude, longitude, allowed_radius_metres 
FROM hospitals 
WHERE hospital_name = 'Head office';
