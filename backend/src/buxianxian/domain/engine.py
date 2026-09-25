"""Pure deterministic command dispatch and atomic state-transition handlers."""

from collections.abc import Iterable
from dataclasses import replace
from typing import assert_never

from buxianxian.domain.cultivation import (
    MAX_SEEK_WHEEL_DAYS,
    WHEEL_SUSPECTED_SIGHTING_THRESHOLD,
    CultivationState,
    SeekWheel,
    WheelSeekingCompleted,
    WheelSeekingStatus,
    settle_wheel_seeking_day,
)
from buxianxian.domain.model import (
    MAX_ADVANCE_DAYS,
    MAX_ELAPSED_DAYS,
    Accepted,
    AdvanceTime,
    Command,
    GameState,
    Rejected,
    RejectionReason,
    TimeAdvanced,
    TransitionResult,
)
from buxianxian.domain.random_source import RandomSource
from buxianxian.domain.storage import (
    BACKPACK_CAPACITY,
    MAX_ITEM_STACK_QUANTITY,
    PROTOTYPE_ITEM_IDS,
    ItemTransferred,
    RetrieveItem,
    StorageLocation,
    StorageState,
    StoreItem,
    quantity_of,
    with_quantity,
)


class DomainEngine:
    """Dispatch typed commands without owning state or external resources."""

    def __init__(self, known_item_ids: Iterable[str] = PROTOTYPE_ITEM_IDS) -> None:
        item_ids = tuple(known_item_ids)
        if not item_ids or len(set(item_ids)) != len(item_ids):
            raise ValueError("known item IDs must be non-empty and unique")
        self._known_item_ids = frozenset(item_ids)

    def transition(
        self,
        state: GameState,
        command: Command,
        random_source: RandomSource,
    ) -> TransitionResult:
        """Apply one command atomically to an immutable input state."""

        match command:
            case AdvanceTime():
                return _handle_advance_time(state, command)
            case SeekWheel():
                return _handle_seek_wheel(state, command, random_source)
            case StoreItem():
                return self._handle_store_item(state, command)
            case RetrieveItem():
                return self._handle_retrieve_item(state, command)

        assert_never(command)

    def _handle_store_item(
        self,
        state: GameState,
        command: StoreItem,
    ) -> TransitionResult:
        return _handle_item_transfer(
            state=state,
            item_id=command.item_id,
            quantity=command.quantity,
            source=StorageLocation.BACKPACK,
            known_item_ids=self._known_item_ids,
        )

    def _handle_retrieve_item(
        self,
        state: GameState,
        command: RetrieveItem,
    ) -> TransitionResult:
        return _handle_item_transfer(
            state=state,
            item_id=command.item_id,
            quantity=command.quantity,
            source=StorageLocation.WAREHOUSE,
            known_item_ids=self._known_item_ids,
        )


def _handle_advance_time(state: GameState, command: AdvanceTime) -> TransitionResult:
    if type(command.days) is not int or command.days <= 0:
        return Rejected(state=state, reason=RejectionReason.INVALID_DAY_COUNT)
    if command.days > MAX_ADVANCE_DAYS:
        return Rejected(state=state, reason=RejectionReason.DAY_COUNT_OUT_OF_RANGE)
    if state.elapsed_days > MAX_ELAPSED_DAYS - command.days:
        return Rejected(state=state, reason=RejectionReason.DAY_COUNT_OUT_OF_RANGE)

    current_elapsed_days = state.elapsed_days + command.days
    new_state = replace(
        state,
        revision=state.revision + 1,
        elapsed_days=current_elapsed_days,
    )
    return Accepted(
        state=new_state,
        events=(
            TimeAdvanced(
                previous_elapsed_days=state.elapsed_days,
                current_elapsed_days=current_elapsed_days,
                days_elapsed=command.days,
            ),
        ),
    )


def _handle_seek_wheel(
    state: GameState,
    command: SeekWheel,
    random_source: RandomSource,
) -> TransitionResult:
    if type(command.max_days) is not int or command.max_days <= 0:
        return Rejected(
            state=state,
            reason=RejectionReason.INVALID_SEEK_WHEEL_DAY_COUNT,
        )
    if command.max_days > MAX_SEEK_WHEEL_DAYS:
        return Rejected(
            state=state,
            reason=RejectionReason.SEEK_WHEEL_DAY_COUNT_OUT_OF_RANGE,
        )
    if state.cultivation.wheel_status is WheelSeekingStatus.SUSPECTED_SIGHTING:
        return Rejected(state=state, reason=RejectionReason.WHEEL_ALREADY_SUSPECTED)
    if state.elapsed_days > MAX_ELAPSED_DAYS - command.max_days:
        return Rejected(
            state=state,
            reason=RejectionReason.SEEK_WHEEL_DAY_COUNT_OUT_OF_RANGE,
        )

    insight = state.cultivation.wheel_insight
    ordinary_total = 0
    inspiration_total = 0
    actual_days = 0
    for _ in range(command.max_days):
        settlement = settle_wheel_seeking_day(
            comprehension=state.player.aptitudes.comprehension,
            spiritual_sense=state.player.aptitudes.spiritual_sense,
            temperament=state.player.aptitudes.temperament,
            fortune=state.player.aptitudes.fortune,
            random_source=random_source,
        )
        actual_days += 1
        remaining = WHEEL_SUSPECTED_SIGHTING_THRESHOLD - insight
        ordinary_applied = min(settlement.ordinary_insight, remaining)
        insight += ordinary_applied
        ordinary_total += ordinary_applied

        remaining = WHEEL_SUSPECTED_SIGHTING_THRESHOLD - insight
        inspiration_applied = min(settlement.inspiration_insight, remaining)
        insight += inspiration_applied
        inspiration_total += inspiration_applied
        if insight == WHEEL_SUSPECTED_SIGHTING_THRESHOLD:
            break

    reached_suspected_sighting = insight == WHEEL_SUSPECTED_SIGHTING_THRESHOLD
    current_elapsed_days = state.elapsed_days + actual_days
    new_state = replace(
        state,
        revision=state.revision + 1,
        elapsed_days=current_elapsed_days,
        cultivation=CultivationState(
            stage=state.cultivation.stage,
            wheel_insight=insight,
            wheel_status=(
                WheelSeekingStatus.SUSPECTED_SIGHTING
                if reached_suspected_sighting
                else WheelSeekingStatus.SEEKING
            ),
        ),
    )
    return Accepted(
        state=new_state,
        events=(
            WheelSeekingCompleted(
                requested_max_days=command.max_days,
                actual_days_elapsed=actual_days,
                previous_insight=state.cultivation.wheel_insight,
                current_insight=insight,
                ordinary_insight_gained=ordinary_total,
                inspiration_insight_gained=inspiration_total,
                reached_suspected_sighting=reached_suspected_sighting,
                previous_elapsed_days=state.elapsed_days,
                current_elapsed_days=current_elapsed_days,
            ),
        ),
    )


def _handle_item_transfer(
    *,
    state: GameState,
    item_id: str,
    quantity: int,
    source: StorageLocation,
    known_item_ids: frozenset[str],
) -> TransitionResult:
    if type(quantity) is not int or quantity <= 0:
        return Rejected(state=state, reason=RejectionReason.INVALID_ITEM_QUANTITY)
    if quantity > MAX_ITEM_STACK_QUANTITY:
        return Rejected(state=state, reason=RejectionReason.ITEM_QUANTITY_OUT_OF_RANGE)
    if type(item_id) is not str or item_id not in known_item_ids:
        return Rejected(state=state, reason=RejectionReason.UNKNOWN_ITEM)

    source_stacks = (
        state.storage.backpack if source is StorageLocation.BACKPACK else state.storage.warehouse
    )
    target_stacks = (
        state.storage.warehouse if source is StorageLocation.BACKPACK else state.storage.backpack
    )
    source_quantity = quantity_of(source_stacks, item_id)
    if source_quantity < quantity:
        return Rejected(state=state, reason=RejectionReason.SOURCE_ITEM_INSUFFICIENT)

    target_quantity = quantity_of(target_stacks, item_id)
    if target_quantity > MAX_ITEM_STACK_QUANTITY - quantity:
        return Rejected(state=state, reason=RejectionReason.ITEM_QUANTITY_OUT_OF_RANGE)
    if (
        source is StorageLocation.WAREHOUSE
        and target_quantity == 0
        and len(target_stacks) >= BACKPACK_CAPACITY
    ):
        return Rejected(state=state, reason=RejectionReason.BACKPACK_CAPACITY_EXCEEDED)

    source_quantity_after = source_quantity - quantity
    target_quantity_after = target_quantity + quantity
    updated_source = with_quantity(source_stacks, item_id, source_quantity_after)
    updated_target = with_quantity(target_stacks, item_id, target_quantity_after)
    if source is StorageLocation.BACKPACK:
        storage = StorageState(backpack=updated_source, warehouse=updated_target)
        target = StorageLocation.WAREHOUSE
    else:
        storage = StorageState(backpack=updated_target, warehouse=updated_source)
        target = StorageLocation.BACKPACK

    return Accepted(
        state=replace(state, revision=state.revision + 1, storage=storage),
        events=(
            ItemTransferred(
                item_id=item_id,
                quantity=quantity,
                source=source,
                target=target,
                source_quantity_after=source_quantity_after,
                target_quantity_after=target_quantity_after,
            ),
        ),
    )
