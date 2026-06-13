from __future__ import annotations

from dataclasses import dataclass
import math

from app.core.physics_engine import (
    PhysicsValidationError,
    SimulationParameters,
    SimulationResult,
    simulate_projectile,
)


__all__ = [
    "TankSimulationValidationError",
    "TankShotParameters",
    "TankShotResult",
    "validate_tank_parameters",
    "simulate_tank_shot",
]


class TankSimulationValidationError(ValueError):
    """Geçersiz kara platformu simülasyon verilerini bildirir."""


@dataclass(frozen=True, slots=True)
class TankShotParameters:
    """Kara platformu atış simülasyonunun giriş değerlerini taşır."""

    initial_speed_m_s: float
    launch_angle_deg: float
    target_distance_m: float
    start_x_m: float = 0.0
    barrel_height_m: float = 2.5
    ground_level_m: float = 0.0
    wind_speed_m_s: float = 0.0
    linear_drag_coefficient: float = 0.0
    hit_radius_m: float = 10.0
    gravity_m_s2: float = 9.81
    time_step_s: float = 0.02
    max_time_s: float = 120.0


@dataclass(frozen=True, slots=True)
class TankShotResult:
    """Kara platformu atış simülasyonunun sonucunu taşır."""

    trajectory: SimulationResult
    target_x_m: float
    impact_x_m: float | None
    signed_deviation_m: float | None
    absolute_deviation_m: float | None
    is_hit: bool


def _require_finite_number(name: str, value: object) -> float:
    """Değerin bool olmayan sonlu bir sayı olduğunu doğrular."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TankSimulationValidationError(
            f"{name} sayısal bir değer olmalıdır."
        )

    numeric_value = float(value)
    if not math.isfinite(numeric_value):
        raise TankSimulationValidationError(
            f"{name} sonlu bir değer olmalıdır."
        )

    return numeric_value


def validate_tank_parameters(parameters: TankShotParameters) -> None:
    """Kara platformu simülasyon parametrelerini doğrular."""
    if not isinstance(parameters, TankShotParameters):
        raise TankSimulationValidationError(
            "Geçerli bir TankShotParameters nesnesi gereklidir."
        )

    initial_speed = _require_finite_number(
        "Başlangıç sürati",
        parameters.initial_speed_m_s,
    )
    launch_angle = _require_finite_number(
        "Fırlatma açısı",
        parameters.launch_angle_deg,
    )
    target_distance = _require_finite_number(
        "Hedef mesafesi",
        parameters.target_distance_m,
    )
    _require_finite_number(
        "Başlangıç x konumu",
        parameters.start_x_m,
    )
    barrel_height = _require_finite_number(
        "Namlu yüksekliği",
        parameters.barrel_height_m,
    )
    ground_level = _require_finite_number(
        "Zemin yüksekliği",
        parameters.ground_level_m,
    )
    wind_speed = _require_finite_number(
        "Rüzgâr hızı",
        parameters.wind_speed_m_s,
    )
    drag = _require_finite_number(
        "Direnç katsayısı",
        parameters.linear_drag_coefficient,
    )
    hit_radius = _require_finite_number(
        "İsabet yarıçapı",
        parameters.hit_radius_m,
    )
    gravity = _require_finite_number(
        "Yerçekimi ivmesi",
        parameters.gravity_m_s2,
    )
    time_step = _require_finite_number(
        "Zaman adımı",
        parameters.time_step_s,
    )
    max_time = _require_finite_number(
        "Azami süre",
        parameters.max_time_s,
    )

    if not 1.0 <= initial_speed <= 500.0:
        raise TankSimulationValidationError(
            "Başlangıç sürati 1 ile 500 m/s arasında olmalıdır."
        )
    if not 0.0 <= launch_angle <= 85.0:
        raise TankSimulationValidationError(
            "Fırlatma açısı 0 ile 85 derece arasında olmalıdır."
        )
    if not 1.0 <= target_distance <= 10000.0:
        raise TankSimulationValidationError(
            "Hedef mesafesi 1 ile 10000 metre arasında olmalıdır."
        )
    if barrel_height < ground_level:
        raise TankSimulationValidationError(
            "Namlu yüksekliği zemin seviyesinden düşük olamaz."
        )
    if barrel_height - ground_level > 100.0:
        raise TankSimulationValidationError(
            "Namlu yüksekliği zeminin en fazla 100 metre üzerinde olabilir."
        )
    if not -100.0 <= wind_speed <= 100.0:
        raise TankSimulationValidationError(
            "Rüzgâr hızı -100 ile 100 m/s arasında olmalıdır."
        )
    if not 0.0 <= drag <= 2.0:
        raise TankSimulationValidationError(
            "Direnç katsayısı 0 ile 2 arasında olmalıdır."
        )
    if not 0.1 <= hit_radius <= 500.0:
        raise TankSimulationValidationError(
            "İsabet yarıçapı 0.1 ile 500 metre arasında olmalıdır."
        )
    if not 0.0 < gravity <= 50.0:
        raise TankSimulationValidationError(
            "Yerçekimi ivmesi 0 ile 50 m/s² arasında olmalıdır."
        )
    if not 0.001 <= time_step <= 0.1:
        raise TankSimulationValidationError(
            "Zaman adımı 0.001 ile 0.1 saniye arasında olmalıdır."
        )
    if not time_step < max_time <= 600.0:
        raise TankSimulationValidationError(
            "Azami süre zaman adımından büyük ve en fazla 600 olmalıdır."
        )


def _to_simulation_parameters(
    parameters: TankShotParameters,
) -> SimulationParameters:
    """Kara platformu değerlerini ortak fizik parametrelerine dönüştürür."""
    return SimulationParameters(
        initial_speed_m_s=parameters.initial_speed_m_s,
        launch_angle_deg=parameters.launch_angle_deg,
        start_x_m=parameters.start_x_m,
        start_y_m=parameters.barrel_height_m,
        ground_level_m=parameters.ground_level_m,
        gravity_m_s2=parameters.gravity_m_s2,
        wind_speed_m_s=parameters.wind_speed_m_s,
        linear_drag_coefficient=parameters.linear_drag_coefficient,
        time_step_s=parameters.time_step_s,
        max_time_s=parameters.max_time_s,
    )


def simulate_tank_shot(
    parameters: TankShotParameters,
) -> TankShotResult:
    """Ortak fizik motoruyla kara platformu atış sonucunu hesaplar."""
    validate_tank_parameters(parameters)

    simulation_parameters = _to_simulation_parameters(parameters)

    try:
        trajectory = simulate_projectile(simulation_parameters)
    except PhysicsValidationError as error:
        raise TankSimulationValidationError(
            "Fizik simülasyonu geçerli bir sonuç üretemedi."
        ) from error

    target_x_m = parameters.start_x_m + parameters.target_distance_m
    if not math.isfinite(target_x_m):
        raise TankSimulationValidationError(
            "Hesaplanan hedef konumu sonlu olmalıdır."
        )

    if not trajectory.landed:
        return TankShotResult(
            trajectory=trajectory,
            target_x_m=target_x_m,
            impact_x_m=None,
            signed_deviation_m=None,
            absolute_deviation_m=None,
            is_hit=False,
        )

    if not trajectory.points:
        raise TankSimulationValidationError(
            "Çarpışma sonucu için yörünge noktası bulunamadı."
        )

    impact_x_m = trajectory.points[-1].x_m
    signed_deviation_m = impact_x_m - target_x_m
    absolute_deviation_m = abs(signed_deviation_m)

    if not all(
        math.isfinite(value)
        for value in (
            impact_x_m,
            signed_deviation_m,
            absolute_deviation_m,
        )
    ):
        raise TankSimulationValidationError(
            "Çarpışma ve sapma değerleri sonlu olmalıdır."
        )

    is_hit = absolute_deviation_m <= parameters.hit_radius_m

    return TankShotResult(
        trajectory=trajectory,
        target_x_m=target_x_m,
        impact_x_m=impact_x_m,
        signed_deviation_m=signed_deviation_m,
        absolute_deviation_m=absolute_deviation_m,
        is_hit=is_hit,
    )