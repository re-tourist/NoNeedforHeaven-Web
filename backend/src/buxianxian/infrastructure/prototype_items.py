"""Small pre-alpha product item catalog for the playable storage slice."""

from buxianxian.domain import (
    COMMON_HERB_ID,
    DRY_FOOD_ID,
    LOW_SPIRIT_STONE_ID,
    TATTERED_SCROLL_ID,
    ItemDefinition,
)

PROTOTYPE_ITEM_CATALOG: tuple[ItemDefinition, ...] = (
    ItemDefinition(
        item_id=LOW_SPIRIT_STONE_ID,
        name="下品灵石",
        description="常见的低阶灵石。当前版本仅可存放与取回。",
        category="灵石",
    ),
    ItemDefinition(
        item_id=DRY_FOOD_ID,
        name="干粮",
        description="便于携带的简单食物。当前版本尚无使用效果。",
        category="补给",
    ),
    ItemDefinition(
        item_id=COMMON_HERB_ID,
        name="普通药草",
        description="随处可见的药草材料。当前版本尚无炼制用途。",
        category="材料",
    ),
    ItemDefinition(
        item_id=TATTERED_SCROLL_ID,
        name="残旧纸卷",
        description="字迹模糊的旧纸卷。当前版本尚不能阅读或使用。",
        category="文档",
    ),
)
