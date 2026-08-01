from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/simulation", tags=["Simulation"])


class SimulationRequest(BaseModel):
    temp_delta_celsius: float = Field(
        ...,
        description="Temperature variance in °C",
        examples=[2.5],
    )
    rainfall_percentage_change: float = Field(
        ...,
        description="Percentage change in rainfall",
        examples=[20.0],
    )
    sea_level_rise_meters: float = Field(
        0.0,
        description="Sea level surge in meters",
        examples=[0.4],
    )
    target_region: str = Field(
        "NATIONAL",
        description="Target state or region",
        examples=["Tamil Nadu"],
    )


class SimulationResponse(BaseModel):
    region: str
    simulated_flood_risk_score: float
    simulated_heatwave_index: float
    affected_districts_count: int
    recommendation: str


@router.post("/run", response_model=SimulationResponse)
async def run_climate_simulation(payload: SimulationRequest):
    try:
        base_flood_risk = 45.0
        base_heat_risk = 50.0

        # Bound risk scores between 0.0 and 100.0
        calculated_flood_risk = max(
            0.0,
            min(
                100.0,
                base_flood_risk
                + (payload.rainfall_percentage_change * 1.5)
                + (payload.sea_level_rise_meters * 20.0),
            ),
        )

        calculated_heat_risk = max(
            0.0,
            min(
                100.0,
                base_heat_risk + (payload.temp_delta_celsius * 12.0),
            ),
        )

        affected_districts = int(
            (calculated_flood_risk + calculated_heat_risk) / 10
        )

        # Dynamic Recommendation Logic
        if calculated_flood_risk > 75.0:
            recommendation = (
                "CRITICAL: Prepare coastal drainage systems and issue"
                " district-level flood advisories."
            )
        elif calculated_heat_risk > 70.0:
            recommendation = (
                "WARNING: Implement heat action plans for outdoor workforce."
            )
        else:
            recommendation = "Normal operations."

        return SimulationResponse(
            region=payload.target_region,
            simulated_flood_risk_score=round(calculated_flood_risk, 2),
            simulated_heatwave_index=round(calculated_heat_risk, 2),
            affected_districts_count=affected_districts,
            recommendation=recommendation,
        )

    except Exception as e:
        # Prevents hiding standard HTTP exceptions while catching unexpected runtime errors
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")