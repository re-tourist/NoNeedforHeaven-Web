"""High-risk contracts for immutable backpack and warehouse transfers."""

import pytest

from buxianxian.domain import (
    BACKPACK_CAPACITY,
    COMMON_HERB_ID,
    DRY_FOOD_ID,
    LOW_SPIRIT_STONE_ID,
    TATTERED_SCROLL_ID,
    Accepted,
    DomainEngine,
    GameState,
    InnateAptitudes,
    ItemStack,
    ItemTransferred,
    PlayerCharacter,
    Rejected,
    RejectionReason,
    RetrieveItem,
    StorageLocation,
    StorageState,
    StoreItem,
    quantity_of,
)


class NeverRandomSource:
    """Prove item transfers never consume the game random sequence."""

    def integer_inclusive(self, minimum: int, maximum: int, /) -> int:
        raise AssertionError(f"unexpected random request: [{minimum}, {maximum}]")


PLAYER = PlayerCharacter(
    name="测试角色",
    aptitudes=InnateAptitudes(5, 5, 5, 5, 5),
    trait_ids=("trait.alpha", "trait.beta"),
)


def _state(
    *,
    revision: int = 4,
    elapsed_days: int = 9,
    storage: StorageState | None = None,
) -> GameState:
    return GameState(
        revision=revision,
        elapsed_days=elapsed_days,
        player=PLAYER,
        storage=StorageState.initial() if storage is None else storage,
    )


def _total_quantity(state: GameState, item_id: str) -> int:
    return quantity_of(state.storage.backpack, item_id) + quantity_of(
        state.storage.warehouse,
        item_id,
    )


def test_new_game_storage_contains_the_pre_alpha_initial_items() -> None:
    storage = StorageState.initial()

    assert storage == StorageState(
        backpack=(
            ItemStack(TATTERED_SCROLL_ID, 1),
            ItemStack(COMMON_HERB_ID, 3),
            ItemStack(DRY_FOOD_ID, 5),
            ItemStack(LOW_SPIRIT_STONE_ID, 20),
        ),
        warehouse=(),
    )


def test_store_item_is_atomic_conserves_quantity_and_does_not_use_time_or_rng() -> None:
    state = _state()

    result = DomainEngine().transition(
        state,
        StoreItem(item_id=LOW_SPIRIT_STONE_ID, quantity=10),
        NeverRandomSource(),
    )

    assert result == Accepted(
        state=_state(
            revision=5,
            storage=StorageState(
                backpack=(
                    ItemStack(TATTERED_SCROLL_ID, 1),
                    ItemStack(COMMON_HERB_ID, 3),
                    ItemStack(DRY_FOOD_ID, 5),
                    ItemStack(LOW_SPIRIT_STONE_ID, 10),
                ),
                warehouse=(ItemStack(LOW_SPIRIT_STONE_ID, 10),),
            ),
        ),
        events=(
            ItemTransferred(
                item_id=LOW_SPIRIT_STONE_ID,
                quantity=10,
                source=StorageLocation.BACKPACK,
                target=StorageLocation.WAREHOUSE,
                source_quantity_after=10,
                target_quantity_after=10,
            ),
        ),
    )
    assert result.state is not state
    assert result.state.elapsed_days == state.elapsed_days
    assert _total_quantity(result.state, LOW_SPIRIT_STONE_ID) == 20
    assert state == _state()


def test_retrieve_item_conserves_quantity_and_removes_empty_warehouse_stack() -> None:
    starting = DomainEngine().transition(
        _state(),
        StoreItem(item_id=LOW_SPIRIT_STONE_ID, quantity=10),
        NeverRandomSource(),
    )
    assert isinstance(starting, Accepted)

    result = DomainEngine().transition(
        starting.state,
        RetrieveItem(item_id=LOW_SPIRIT_STONE_ID, quantity=10),
        NeverRandomSource(),
    )

    assert isinstance(result, Accepted)
    assert result.state.revision == 6
    assert result.state.elapsed_days == 9
    assert quantity_of(result.state.storage.backpack, LOW_SPIRIT_STONE_ID) == 20
    assert result.state.storage.warehouse == ()
    assert _total_quantity(result.state, LOW_SPIRIT_STONE_ID) == 20


@pytest.mark.parametrize(
    ("command", "reason"),
    [
        (
            StoreItem(item_id=LOW_SPIRIT_STONE_ID, quantity=0),
            RejectionReason.INVALID_ITEM_QUANTITY,
        ),
        (
            StoreItem(item_id=LOW_SPIRIT_STONE_ID, quantity=-1),
            RejectionReason.INVALID_ITEM_QUANTITY,
        ),
        (
            StoreItem(item_id="unknown.item", quantity=1),
            RejectionReason.UNKNOWN_ITEM,
        ),
        (
            StoreItem(item_id=LOW_SPIRIT_STONE_ID, quantity=21),
            RejectionReason.SOURCE_ITEM_INSUFFICIENT,
        ),
        (
            RetrieveItem(item_id=LOW_SPIRIT_STONE_ID, quantity=1),
            RejectionReason.SOURCE_ITEM_INSUFFICIENT,
        ),
    ],
)
def test_invalid_transfer_is_structurally_rejected_without_mutation(
    command: StoreItem | RetrieveItem,
    reason: RejectionReason,
) -> None:
    state = _state()

    result = DomainEngine().transition(state, command, NeverRandomSource())

    assert result == Rejected(state=state, reason=reason)
    assert result.state is state
    assert state == _state()


def test_retrieve_new_item_is_rejected_when_backpack_has_twelve_distinct_items() -> None:
    backpack_ids = tuple(f"test.item_{index:02d}" for index in range(BACKPACK_CAPACITY))
    warehouse_id = "test.warehouse_item"
    storage = StorageState(
        backpack=tuple(ItemStack(item_id, 1) for item_id in backpack_ids),
        warehouse=(ItemStack(warehouse_id, 2),),
    )
    state = _state(storage=storage)
    engine = DomainEngine((*backpack_ids, warehouse_id))

    result = engine.transition(
        state,
        RetrieveItem(item_id=warehouse_id, quantity=1),
        NeverRandomSource(),
    )

    assert result == Rejected(
        state=state,
        reason=RejectionReason.BACKPACK_CAPACITY_EXCEEDED,
    )
    assert result.state is state
