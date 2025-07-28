# app/schemas/workout_progress.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class UserProfileSummary(BaseModel):
    weight: str
    period: str

class OverviewSummary(BaseModel):
    overviewSummary: List[str]

class ConsistencyAnalysis(BaseModel):
    completedDays: int
    totalDays: int
    consistencyPercentage: float
    summary: str

class IntensityAndVolumeTrends(BaseModel):
    averageRPE: Optional[float]
    totalSets: int
    totalReps: int
    weightLiftedSummary: str

class MuscleGroupFocus(BaseModel):
    muscleGroupDistribution: Dict[str, int]
    summary: str

class TrainingFeedback(BaseModel):
    area: str
    points: List[str]

class Suggestion(BaseModel):
    title: str
    tips: List[str]

class InsightsAndRecommendations(BaseModel):
    trainingFeedback: List[TrainingFeedback]
    suggestions: List[Suggestion]

class WorkoutProgressReport(BaseModel):
    userProfile: UserProfileSummary
    overviewSummary: List[str]
    consistencyAnalysis: ConsistencyAnalysis
    intensityAndVolumeTrends: IntensityAndVolumeTrends
    muscleGroupFocus: MuscleGroupFocus
    insightsAndRecommendations: InsightsAndRecommendations
    conclusion: str
