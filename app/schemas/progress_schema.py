from pydantic import BaseModel, Field
from typing import List, Optional


class CalorieDetails(BaseModel):
    breakfast: int
    lunch: int
    dinner: int
    total: int


class DailyCalorieLog(BaseModel):
    date: str  # Format: YYYY-MM-DD
    calories: CalorieDetails


class DailyAverages(BaseModel):
    breakfast: int
    lunch: int
    dinner: int
    totalDaily: int


class VisualizationChart(BaseModel):
    type: str
    description: str


class VisualizationSuggestion(BaseModel):
    title: str
    charts: List[VisualizationChart]


class EstimatedCalorieBreakdown(BaseModel):
    notes: str
    dailyAverages: DailyAverages
    dailyLog: List[DailyCalorieLog]
    visualizationSuggestion: VisualizationSuggestion


class MealLoggingConsistency(BaseModel):
    consistencyPercentage: float
    summary: str
    missedMeals: str


class AdherenceAnalysis(BaseModel):
    adherencePercentage: float
    summary: str
    bestAdherenceDays: str
    consumptionPattern: str


class NutritionalFeedbackItem(BaseModel):
    area: str  # "Positives" or "Areas for Improvement"
    points: List[str]


class Recommendation(BaseModel):
    title: str
    suggestions: Optional[List[str]] = None
    example: Optional[str] = None


class InsightsAndRecommendations(BaseModel):
    nutritionalFeedback: List[NutritionalFeedbackItem]
    recommendations: List[Recommendation]


class UserProfileInfo(BaseModel):
    weight: str
    period: str


class DietProgressReport(BaseModel):
    userProfile: UserProfileInfo
    overviewSummary: List[str]
    estimatedCalorieBreakdown: EstimatedCalorieBreakdown
    mealLoggingConsistency: MealLoggingConsistency
    adherenceAnalysis: AdherenceAnalysis
    insightsAndRecommendations: InsightsAndRecommendations
    conclusion: str


class AiProgressSummary(BaseModel):
    dietProgressReport: DietProgressReport


class AiProgressResponse(BaseModel):
    start_date: str
    end_date: str
    summary: AiProgressSummary
