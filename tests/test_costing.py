from app.costing import estimate_profile_cost


def test_cost_estimate_stays_under_one_cent_for_30_seconds() -> None:
    assert estimate_profile_cost(30, use_openai=True, transcribe_model="gpt-4o-transcribe-diarize") < 0.01
