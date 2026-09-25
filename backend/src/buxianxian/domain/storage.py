"""Immutable item storage values and typed transfer contracts."""

import re
from dataclasses import dataclass
from enum import StrEnum

BACKPACK_CAPACITY = 12
MAX_ITEM_STACK_QUANTITY = 1_000_000_000

LOW_SPIRIT_STONE_ID = "spirit_stone.low"
DRY_FOOD_ID = "provision.dry_food"
COMMON_HERB_ID = "material.common_herb"
TATTERED_SCROLL_ID = "document.tattered_scroll"
PROTOTYPE_ITEM_IDS = (
    COMMON_HERB_ID,
    TATTERED_SCROLL_ID,
    DRY_FOOD_ID,
    LOW_SPIRIT_STONE_ID,
)

_ITEM_ID_PATTERN = re.compile(r"[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*")


class StorageLocation(StrEnum):
    """Stable container identities used by transfer facts."""

    BACKPACK = "backpack"
    WAREHOUSE = "warehouse"


@dataclass(frozen=True, slots=True)
class ItemStack:
    """One positive quantity of a stable item identity."""

    item_id: str
    quantity: int

    def __post_init__(self) -> None:
        if not is_valid_item_id(self.item_id):
            raise ValueError("item_id must be a valid stable machine ID")
        if (
            type(self.quantity) is not int
            or self.quantity <= 0
            or self.quantity > MAX_ITEM_STACK_QUANTITY
        ):
            raise ValueError("item quantity must be a positive bounded integer")


@dataclass(frozen=True, slots=True)
class StorageState:
    """Canonical immutable backpack and warehouse contents."""

    backpack: tuple[ItemStack, ...]
    warehouse: tuple[ItemStack, ...]

    def __post_init__(self) -> None:
        _validate_stacks(self.backpack, "backpack")
        _validate_stacks(self.warehouse, "warehouse")
        if len(self.backpack) > BACKPACK_CAPACITY:
            raise ValueError("backpack exceeds its distinct-item capacity")

    @classmethod
    def initial(cls) -> StorageState:
        """Return the pre-alpha new-game inventory."""

        return cls(
            backpack=_canonical_stacks(
                (
                    ItemStack(LOW_SPIRIT_STONE_ID, 20),
                    ItemStack(DRY_FOOD_ID, 5),
                    ItemStack(COMMON_HERB_ID, 3),
                    ItemStack(TATTERED_SCROLL_ID, 1),
                )
            ),
            warehouse=(),
        )


@dataclass(frozen=True, slots=True)
class StoreItem:
    """Request a quantity transfer from backpack to warehouse."""

    item_id: str
    quantity: int


@dataclass(frozen=True, slots=True)
class RetrieveItem:
    """Request a quantity transfer from warehouse to backpack."""

    item_id: str
    quantity: int


@dataclass(frozen=True, slots=True)
class ItemTransferred:
    """Fact that one item quantity moved atomically between containers."""

    item_id: str
    quantity: int
    source: StorageLocation
    target: StorageLocation
    source_quantity_after: int
    target_quantity_after: int


@dataclass(frozen=True, slots=True)
class ItemDefinition:
    """Static display metadata kept outside player save state."""

    item_id: str
    name: str
    description: str
    category: str

    def __post_init__(self) -> None:
        if not is_valid_item_id(self.item_id):
            raise ValueError("item definition ID must be a valid stable machine ID")
        if any(
            type(value) is not str or not value or value != value.strip()
            for value in (self.name, self.description, self.category)
        ):
            raise ValueError("item definition text must be non-empty and trimmed")


def is_valid_item_id(item_id: str) -> bool:
    """Return whether an item ID is stable and portable."""

    return (
        type(item_id) is str
        and len(item_id) <= 128
        and _ITEM_ID_PATTERN.fullmatch(item_id) is not None
    )


def quantity_of(stacks: tuple[ItemStack, ...], item_id: str) -> int:
    """Read a quantity without exposing a mutable mapping."""

    return next((stack.quantity for stack in stacks if stack.item_id == item_id), 0)


def with_quantity(
    stacks: tuple[ItemStack, ...],
    item_id: str,
    quantity: int,
) -> tuple[ItemStack, ...]:
    """Return canonical stacks with one item quantity replaced or removed."""

    remaining = tuple(stack for stack in stacks if stack.item_id != item_id)
    if quantity == 0:
        return remaining
    return _canonical_stacks((*remaining, ItemStack(item_id=item_id, quantity=quantity)))


def _canonical_stacks(stacks: tuple[ItemStack, ...]) -> tuple[ItemStack, ...]:
    return tuple(sorted(stacks, key=lambda stack: stack.item_id))


def _validate_stacks(stacks: tuple[ItemStack, ...], label: str) -> None:
    if type(stacks) is not tuple or any(type(stack) is not ItemStack for stack in stacks):
        raise ValueError(f"{label} must be a tuple of ItemStack values")
    item_ids = tuple(stack.item_id for stack in stacks)
    if len(set(item_ids)) != len(item_ids):
        raise ValueError(f"{label} item IDs must be unique")
    if item_ids != tuple(sorted(item_ids)):
        raise ValueError(f"{label} must use canonical item ID order")
