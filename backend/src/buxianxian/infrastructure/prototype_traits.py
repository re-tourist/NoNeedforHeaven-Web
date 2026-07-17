"""Explicit pre-alpha trait labels for the first operable web slice."""

from buxianxian.domain import TraitDefinition

PROTOTYPE_TRAIT_CATALOG: tuple[TraitDefinition, ...] = (
    TraitDefinition(
        trait_id="prototype.adaptable",
        name="灵活",
        description="面对变化时愿意调整方法。当前版本不附带规则效果。",
    ),
    TraitDefinition(
        trait_id="prototype.calm",
        name="沉着",
        description="遇到压力时倾向保持冷静。当前版本不附带规则效果。",
    ),
    TraitDefinition(
        trait_id="prototype.decisive",
        name="果断",
        description="作出选择时较少犹豫。当前版本不附带规则效果。",
    ),
    TraitDefinition(
        trait_id="prototype.diligent",
        name="勤勉",
        description="愿意持续投入精力。当前版本不附带规则效果。",
    ),
    TraitDefinition(
        trait_id="prototype.focused",
        name="专注",
        description="处理事务时倾向集中注意。当前版本不附带规则效果。",
    ),
    TraitDefinition(
        trait_id="prototype.observant",
        name="善察",
        description="习惯留意周围细节。当前版本不附带规则效果。",
    ),
    TraitDefinition(
        trait_id="prototype.patient",
        name="耐心",
        description="面对缓慢进展时愿意等待。当前版本不附带规则效果。",
    ),
    TraitDefinition(
        trait_id="prototype.steady",
        name="稳健",
        description="行动时倾向采用稳妥步骤。当前版本不附带规则效果。",
    ),
)
