from __future__ import annotations

from dataclasses import dataclass
import math


__all__ = [
    "PhysicsValidationError",
    "SimulationParameters",
    "TrajectoryPoint",
    "SimulationResult",
    "validate_parameters",
    "simulate_projectile",
]


class PhysicsValidationError(ValueError):
    """Geçersiz simülasyon parametrelerini bildirir."""


@dataclass(frozen=True, slots=True)
class SimulationParameters:
    """İki boyutlu yörünge simülasyonunun giriş parametreleri."""

    initial_speed_m_s: float
    launch_angle_deg: float
    start_x_m: float = 0.0
    start_y_m: float = 0.0
    ground_level_m: float = 0.0
    gravity_m_s2: float = 9.81
    wind_speed_m_s: float = 0.0
    linear_drag_coefficient: float = 0.0
    time_step_s: float = 0.02
    max_time_s: float = 120.0


@dataclass(frozen=True, slots=True)
class TrajectoryPoint:
    """Yörüngenin belirli bir andaki durumunu temsil eder."""

    time_s: float
    x_m: float
    y_m: float
    velocity_x_m_s: float
    velocity_y_m_s: float
    speed_m_s: float


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """Tamamlanan yörünge simülasyonunun sonucunu taşır."""

    points: tuple[TrajectoryPoint, ...]
    flight_time_s: float
    horizontal_range_m: float
    maximum_height_m: float
    impact_speed_m_s: float | None
    landed: bool
    termination_reason: str


def _require_finite_number(name: str, value: object) -> float:
    """Değerin bool olmayan sonlu bir sayı olduğunu doğrular."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PhysicsValidationError(f"{name} sayısal bir değer olmalıdır.")

    numeric_value = float(value)
    if not math.isfinite(numeric_value):
        raise PhysicsValidationError(f"{name} sonlu bir değer olmalıdır.")

    return numeric_value


def validate_parameters(parameters: SimulationParameters) -> None:
    """Simülasyon parametrelerinin geçerli olduğunu doğrular."""
    if not isinstance(parameters, SimulationParameters):
        raise PhysicsValidationError(
            "Geçerli bir SimulationParameters nesnesi gereklidir."
        )

    initial_speed = _require_finite_number(
        "Başlangıç sürati", parameters.initial_speed_m_s
    )
    launch_angle = _require_finite_number(
        "Fırlatma açısı", parameters.launch_angle_deg
    )
    _require_finite_number("Başlangıç x konumu", parameters.start_x_m)
    start_y = _require_finite_number(
        "Başlangıç y konumu", parameters.start_y_m
    )
    ground_level = _require_finite_number(
        "Zemin yüksekliği", parameters.ground_level_m
    )
    gravity = _require_finite_number(
        "Yerçekimi ivmesi", parameters.gravity_m_s2
    )
    wind_speed = _require_finite_number(
        "Rüzgâr hızı", parameters.wind_speed_m_s
    )
    drag = _require_finite_number(
        "Direnç katsayısı", parameters.linear_drag_coefficient
    )
    time_step = _require_finite_number(
        "Zaman adımı", parameters.time_step_s
    )
    max_time = _require_finite_number(
        "Azami süre", parameters.max_time_s
    )

    if not 0.0 < initial_speed <= 2000.0:
        raise PhysicsValidationError(
            "Başlangıç sürati 0 ile 2000 arasında olmalıdır."
        )
    if not -89.0 <= launch_angle <= 89.0:
        raise PhysicsValidationError(
            "Fırlatma açısı -89 ile 89 derece arasında olmalıdır."
        )
    if start_y < ground_level:
        raise PhysicsValidationError(
            "Başlangıç yüksekliği zeminden düşük olamaz."
        )
    if not 0.0 < gravity <= 50.0:
        raise PhysicsValidationError(
            "Yerçekimi ivmesi 0 ile 50 arasında olmalıdır."
        )
    if not -200.0 <= wind_speed <= 200.0:
        raise PhysicsValidationError(
            "Rüzgâr hızı -200 ile 200 arasında olmalıdır."
        )
    if not 0.0 <= drag <= 5.0:
        raise PhysicsValidationError(
            "Direnç katsayısı 0 ile 5 arasında olmalıdır."
        )
    if not 0.001 <= time_step <= 0.1:
        raise PhysicsValidationError(
            "Zaman adımı 0.001 ile 0.1 saniye arasında olmalıdır."
        )
    if not time_step < max_time <= 600.0:
        raise PhysicsValidationError(
            "Azami süre zaman adımından büyük ve en fazla 600 olmalıdır."
        )


def _derivatives(
    state: tuple[float, float, float, float],
    gravity: float,
    wind_speed: float,
    drag: float,
) -> tuple[float, float, float, float]:
    """Konum ve hız durumunun zamana göre türevlerini hesaplar."""
    _, _, velocity_x, velocity_y = state
    acceleration_x = -drag * (velocity_x - wind_speed)
    acceleration_y = -gravity - drag * velocity_y

    return velocity_x, velocity_y, acceleration_x, acceleration_y


def _add_scaled(
    state: tuple[float, float, float, float],
    derivative: tuple[float, float, float, float],
    scale: float,
) -> tuple[float, float, float, float]:
    """Bir duruma ölçeklenmiş türev ekler."""
    return (
        state[0] + derivative[0] * scale,
        state[1] + derivative[1] * scale,
        state[2] + derivative[2] * scale,
        state[3] + derivative[3] * scale,
    )


def _rk4_step(
    state: tuple[float, float, float, float],
    step_s: float,
    gravity: float,
    wind_speed: float,
    drag: float,
) -> tuple[float, float, float, float]:
    """Durumu sabit adımlı dördüncü derece Runge-Kutta ile ilerletir."""
    k1 = _derivatives(state, gravity, wind_speed, drag)
    k2 = _derivatives(
        _add_scaled(state, k1, step_s / 2.0),
        gravity,
        wind_speed,
        drag,
    )
    k3 = _derivatives(
        _add_scaled(state, k2, step_s / 2.0),
        gravity,
        wind_speed,
        drag,
    )
    k4 = _derivatives(
        _add_scaled(state, k3, step_s),
        gravity,
        wind_speed,
        drag,
    )

    factor = step_s / 6.0
    return tuple(
        state[index]
        + factor
        * (
            k1[index]
            + 2.0 * k2[index]
            + 2.0 * k3[index]
            + k4[index]
        )
        for index in range(4)
    )


def _ensure_finite_state(
    time_s: float,
    state: tuple[float, float, float, float],
) -> None:
    """Hesaplanan zaman ve durum değerlerinin sonlu olduğunu doğrular."""
    if not math.isfinite(time_s) or not all(map(math.isfinite, state)):
        raise PhysicsValidationError(
            "Sayısal hesaplama sırasında sonlu olmayan bir değer oluştu."
        )


def _make_point(
    time_s: float,
    state: tuple[float, float, float, float],
) -> TrajectoryPoint:
    """Durum değerlerinden değiştirilemez bir yörünge noktası oluşturur."""
    x, y, velocity_x, velocity_y = state
    return TrajectoryPoint(
        time_s=time_s,
        x_m=x,
        y_m=y,
        velocity_x_m_s=velocity_x,
        velocity_y_m_s=velocity_y,
        speed_m_s=math.hypot(velocity_x, velocity_y),
    )


def simulate_projectile(
    parameters: SimulationParameters,
) -> SimulationResult:
    """Yörüngeyi sabit adımlı dördüncü derece Runge-Kutta ile hesaplar."""
    validate_parameters(parameters)

    angle_rad = math.radians(parameters.launch_angle_deg)
    velocity_x = parameters.initial_speed_m_s * math.cos(angle_rad)
    velocity_y = parameters.initial_speed_m_s * math.sin(angle_rad)

    current_time = 0.0
    current_state = (
        float(parameters.start_x_m),
        float(parameters.start_y_m),
        velocity_x,
        velocity_y,
    )
    _ensure_finite_state(current_time, current_state)

    points = [_make_point(current_time, current_state)]

    if (
        parameters.start_y_m == parameters.ground_level_m
        and velocity_y <= 0.0
    ):
        return SimulationResult(
            points=tuple(points),
            flight_time_s=0.0,
            horizontal_range_m=0.0,
            maximum_height_m=float(parameters.start_y_m),
            impact_speed_m_s=points[0].speed_m_s,
            landed=True,
            termination_reason="ground_impact",
        )

    maximum_steps = math.ceil(
        parameters.max_time_s / parameters.time_step_s
    )

    for _ in range(maximum_steps):
        remaining_time = parameters.max_time_s - current_time
        if remaining_time <= 0.0:
            break

        step_s = min(parameters.time_step_s, remaining_time)
        next_time = current_time + step_s
        next_state = _rk4_step(
            current_state,
            step_s,
            parameters.gravity_m_s2,
            parameters.wind_speed_m_s,
            parameters.linear_drag_coefficient,
        )
        _ensure_finite_state(next_time, next_state)

        current_y = current_state[1]
        next_y = next_state[1]

        if next_y <= parameters.ground_level_m:
            denominator = current_y - next_y
            if denominator > 0.0:
                ratio = (
                    current_y - parameters.ground_level_m
                ) / denominator
            else:
                ratio = 0.0

            ratio = min(1.0, max(0.0, ratio))
            impact_time = current_time + step_s * ratio
            impact_state = (
                current_state[0]
                + (next_state[0] - current_state[0]) * ratio,
                float(parameters.ground_level_m),
                current_state[2]
                + (next_state[2] - current_state[2]) * ratio,
                current_state[3]
                + (next_state[3] - current_state[3]) * ratio,
            )
            _ensure_finite_state(impact_time, impact_state)

            impact_point = _make_point(impact_time, impact_state)
            if impact_time > points[-1].time_s:
                points.append(impact_point)
            else:
                points[-1] = impact_point

            return SimulationResult(
                points=tuple(points),
                flight_time_s=impact_point.time_s,
                horizontal_range_m=(
                    impact_point.x_m - parameters.start_x_m
                ),
                maximum_height_m=max(point.y_m for point in points),
                impact_speed_m_s=impact_point.speed_m_s,
                landed=True,
                termination_reason="ground_impact",
            )

        points.append(_make_point(next_time, next_state))
        current_time = next_time
        current_state = next_state

    final_point = points[-1]
    return SimulationResult(
        points=tuple(points),
        flight_time_s=final_point.time_s,
        horizontal_range_m=final_point.x_m - parameters.start_x_m,
        maximum_height_m=max(point.y_m for point in points),
        impact_speed_m_s=None,
        landed=False,
        termination_reason="max_time_reached",
    )