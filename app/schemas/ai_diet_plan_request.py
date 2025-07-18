from pydantic import BaseModel


class WorkoutPlanRequest(BaseModel):
    veg_or_non_veg: str
    activity_level: str
    fitness_goal: str
    experience_level: str
    medical_conditions: str
    allergies: str
    preferred_workout_style: str
    preferred_training_days_per_week: int
