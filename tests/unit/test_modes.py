from __future__ import annotations

import pytest

from researchforge.models.research import ResearchMode
from researchforge.orchestration.modes import get_mode_config


@pytest.mark.parametrize("mode", list(ResearchMode))
def test_every_mode_has_a_config(mode: ResearchMode):
    config = get_mode_config(mode)
    assert config.mode == mode
    assert config.max_tasks > 0
    assert config.max_parallelism > 0
    assert config.max_iterations >= 1
    assert 0 <= config.quality_threshold <= 100


def test_exhaustive_is_strictly_more_thorough_than_quick():
    quick = get_mode_config(ResearchMode.QUICK)
    exhaustive = get_mode_config(ResearchMode.EXHAUSTIVE)

    assert exhaustive.max_tasks > quick.max_tasks
    assert exhaustive.max_iterations > quick.max_iterations
    assert exhaustive.quality_threshold > quick.quality_threshold
    assert exhaustive.min_evidence_per_task >= quick.min_evidence_per_task
