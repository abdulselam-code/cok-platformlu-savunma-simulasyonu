from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import math
from typing import cast
import unittest
from unittest.mock import patch

from app.core.physics_engine import (
    PhysicsValidationError,
    SimulationResult,
    TrajectoryPoint,
)
from app.simulations.tank_simulation import (
    TankShotParameters,
    TankShotResult,
    TankSimulationValidationError,
    simulate_tank_shot,
    validate_tank_parameters,
)


class TankSimulationTests(unittest.TestCase):
    def _valid_parameters(self) -> TankShotParameters:
        return TankShotParameters(
            initial_speed_m_s=80.0,
            launch_angle_deg=40.0,
            target_distance_m=500.0,
            barrel_height_m=2.5,
            time_step_s=0.02,
        )

    def _impact_distance(self, start_x_m: float = 0.0) -> float:
        result = simulate_tank_shot(
            replace(
                self._valid_parameters(),
                start_x_m=start_x_m,
                target_distance_m=500.0,
            )
        )
        self.assertIsNotNone(result.impact_x_m)
        return cast(float, result.impact_x_m) - start_x_m

    def test_valid_shot_returns_complete_finite_result(self) -> None:
        result = simulate_tank_shot(self._valid_parameters())

        self.assertIsInstance(result, TankShotResult)
        self.assertTrue(result.trajectory.points)
        self.assertTrue(result.trajectory.landed)
        self.assertTrue(math.isfinite(result.target_x_m))
        self.assertIsNotNone(result.impact_x_m)
        self.assertIsNotNone(result.signed_deviation_m)
        self.assertIsNotNone(result.absolute_deviation_m)

        impact_x = cast(float, result.impact_x_m)
        signed_deviation = cast(float, result.signed_deviation_m)
        absolute_deviation = cast(float, result.absolute_deviation_m)

        self.assertTrue(math.isfinite(impact_x))
        self.assertTrue(math.isfinite(signed_deviation))
        self.assertTrue(math.isfinite(absolute_deviation))
        self.assertEqual(absolute_deviation, abs(signed_deviation))
        self.assertIsInstance(result.is_hit, bool)

    def test_target_at_actual_impact_is_a_hit(self) -> None:
        start_x = 125.0
        impact_distance = self._impact_distance(start_x)
        parameters = replace(
            self._valid_parameters(),
            start_x_m=start_x,
            target_distance_m=impact_distance,
            hit_radius_m=0.1,
        )

        result = simulate_tank_shot(parameters)

        self.assertTrue(result.is_hit)
        self.assertIsNotNone(result.absolute_deviation_m)
        self.assertLessEqual(
            cast(float, result.absolute_deviation_m),
            parameters.hit_radius_m,
        )
        self.assertAlmostEqual(
            cast(float, result.signed_deviation_m),
            0.0,
            delta=1e-9,
        )

    def test_impact_before_target_has_negative_deviation(self) -> None:
        impact_distance = self._impact_distance()
        parameters = replace(
            self._valid_parameters(),
            target_distance_m=impact_distance + 100.0,
            hit_radius_m=1.0,
        )

        result = simulate_tank_shot(parameters)

        self.assertFalse(result.is_hit)
        self.assertLess(cast(float, result.signed_deviation_m), 0.0)
        self.assertGreater(cast(float, result.absolute_deviation_m), 0.0)

    def test_impact_beyond_target_has_positive_deviation(self) -> None:
        impact_distance = self._impact_distance()
        target_distance = impact_distance - 100.0
        self.assertGreaterEqual(target_distance, 1.0)

        result = simulate_tank_shot(
            replace(
                self._valid_parameters(),
                target_distance_m=target_distance,
                hit_radius_m=1.0,
            )
        )

        self.assertFalse(result.is_hit)
        self.assertGreater(cast(float, result.signed_deviation_m), 0.0)
        self.assertGreater(cast(float, result.absolute_deviation_m), 0.0)

    def test_deviation_equal_to_hit_radius_is_a_hit(self) -> None:
        initial_parameters = replace(
            self._valid_parameters(),
            target_distance_m=500.0,
            hit_radius_m=1.0,
        )
        initial_result = simulate_tank_shot(initial_parameters)
        exact_deviation = cast(
            float,
            initial_result.absolute_deviation_m,
        )
        self.assertGreaterEqual(exact_deviation, 0.1)
        self.assertLessEqual(exact_deviation, 500.0)

        boundary_result = simulate_tank_shot(
            replace(
                initial_parameters,
                hit_radius_m=exact_deviation,
            )
        )

        self.assertEqual(
            boundary_result.absolute_deviation_m,
            exact_deviation,
        )
        self.assertTrue(boundary_result.is_hit)

    def test_maximum_time_result_has_no_impact_values(self) -> None:
        parameters = TankShotParameters(
            initial_speed_m_s=20.0,
            launch_angle_deg=45.0,
            target_distance_m=100.0,
            barrel_height_m=100.0,
            max_time_s=0.2,
            time_step_s=0.1,
        )

        result = simulate_tank_shot(parameters)

        self.assertFalse(result.trajectory.landed)
        self.assertEqual(
            result.trajectory.termination_reason,
            "max_time_reached",
        )
        self.assertIsNone(result.impact_x_m)
        self.assertIsNone(result.signed_deviation_m)
        self.assertIsNone(result.absolute_deviation_m)
        self.assertFalse(result.is_hit)

    def test_nonzero_start_x_is_used_for_target_and_deviation(self) -> None:
        parameters = replace(
            self._valid_parameters(),
            start_x_m=250.0,
            target_distance_m=400.0,
        )

        result = simulate_tank_shot(parameters)

        expected_target = (
            parameters.start_x_m + parameters.target_distance_m
        )
        expected_deviation = (
            result.trajectory.points[-1].x_m - expected_target
        )

        self.assertEqual(result.target_x_m, expected_target)
        self.assertAlmostEqual(
            cast(float, result.signed_deviation_m),
            expected_deviation,
            places=12,
        )
        self.assertAlmostEqual(
            cast(float, result.absolute_deviation_m),
            abs(expected_deviation),
            places=12,
        )

    def test_parameter_and_result_data_classes_are_immutable(self) -> None:
        parameters = self._valid_parameters()
        result = simulate_tank_shot(parameters)

        with self.assertRaises(FrozenInstanceError):
            setattr(parameters, "initial_speed_m_s", 100.0)

        with self.assertRaises(FrozenInstanceError):
            setattr(result, "is_hit", True)

    def test_non_parameter_object_raises_validation_error(self) -> None:
        invalid_parameters = cast(TankShotParameters, object())

        with self.assertRaises(TankSimulationValidationError):
            validate_tank_parameters(invalid_parameters)

    def test_invalid_initial_speeds_raise_validation_error(self) -> None:
        invalid_values = (
            0.0,
            0.9,
            -1.0,
            500.1,
            True,
            math.nan,
            math.inf,
            -math.inf,
            "100",
            None,
        )

        for value in invalid_values:
            with self.subTest(initial_speed_m_s=value):
                parameters = replace(
                    self._valid_parameters(),
                    initial_speed_m_s=cast(float, value),
                )
                with self.assertRaises(TankSimulationValidationError):
                    validate_tank_parameters(parameters)

    def test_invalid_launch_angles_raise_validation_error(self) -> None:
        invalid_values = (
            -0.1,
            85.1,
            True,
            math.nan,
            math.inf,
            "45",
            None,
        )

        for value in invalid_values:
            with self.subTest(launch_angle_deg=value):
                parameters = replace(
                    self._valid_parameters(),
                    launch_angle_deg=cast(float, value),
                )
                with self.assertRaises(TankSimulationValidationError):
                    validate_tank_parameters(parameters)

    def test_invalid_target_distances_raise_validation_error(self) -> None:
        invalid_values = (
            0.0,
            0.9,
            -1.0,
            10000.1,
            True,
            math.nan,
            math.inf,
            "500",
            None,
        )

        for value in invalid_values:
            with self.subTest(target_distance_m=value):
                parameters = replace(
                    self._valid_parameters(),
                    target_distance_m=cast(float, value),
                )
                with self.assertRaises(TankSimulationValidationError):
                    validate_tank_parameters(parameters)

    def test_invalid_barrel_heights_raise_validation_error(self) -> None:
        invalid_cases = (
            (-0.1, 0.0),
            (100.1, 0.0),
            (True, 0.0),
            (math.nan, 0.0),
            (math.inf, 0.0),
        )

        for barrel_height, ground_level in invalid_cases:
            with self.subTest(
                barrel_height_m=barrel_height,
                ground_level_m=ground_level,
            ):
                parameters = replace(
                    self._valid_parameters(),
                    barrel_height_m=cast(float, barrel_height),
                    ground_level_m=ground_level,
                )
                with self.assertRaises(TankSimulationValidationError):
                    validate_tank_parameters(parameters)

    def test_invalid_wind_speeds_raise_validation_error(self) -> None:
        invalid_values = (
            -100.1,
            100.1,
            True,
            math.nan,
            math.inf,
            "20",
            None,
        )

        for value in invalid_values:
            with self.subTest(wind_speed_m_s=value):
                parameters = replace(
                    self._valid_parameters(),
                    wind_speed_m_s=cast(float, value),
                )
                with self.assertRaises(TankSimulationValidationError):
                    validate_tank_parameters(parameters)

    def test_invalid_drag_coefficients_raise_validation_error(self) -> None:
        invalid_values = (
            -0.1,
            2.1,
            True,
            math.nan,
            math.inf,
            "0.2",
            None,
        )

        for value in invalid_values:
            with self.subTest(linear_drag_coefficient=value):
                parameters = replace(
                    self._valid_parameters(),
                    linear_drag_coefficient=cast(float, value),
                )
                with self.assertRaises(TankSimulationValidationError):
                    validate_tank_parameters(parameters)

    def test_invalid_hit_radii_raise_validation_error(self) -> None:
        invalid_values = (
            0.0,
            0.09,
            -1.0,
            500.1,
            True,
            math.nan,
            math.inf,
            "10",
            None,
        )

        for value in invalid_values:
            with self.subTest(hit_radius_m=value):
                parameters = replace(
                    self._valid_parameters(),
                    hit_radius_m=cast(float, value),
                )
                with self.assertRaises(TankSimulationValidationError):
                    validate_tank_parameters(parameters)

    def test_invalid_gravity_values_raise_validation_error(self) -> None:
        invalid_values = (
            0.0,
            -1.0,
            50.1,
            True,
            math.nan,
            math.inf,
        )

        for value in invalid_values:
            with self.subTest(gravity_m_s2=value):
                parameters = replace(
                    self._valid_parameters(),
                    gravity_m_s2=cast(float, value),
                )
                with self.assertRaises(TankSimulationValidationError):
                    validate_tank_parameters(parameters)

    def test_invalid_time_steps_raise_validation_error(self) -> None:
        invalid_values = (
            0.0,
            0.0009,
            0.1001,
            True,
            math.nan,
            math.inf,
        )

        for value in invalid_values:
            with self.subTest(time_step_s=value):
                parameters = replace(
                    self._valid_parameters(),
                    time_step_s=cast(float, value),
                )
                with self.assertRaises(TankSimulationValidationError):
                    validate_tank_parameters(parameters)

    def test_invalid_maximum_times_raise_validation_error(self) -> None:
        invalid_cases = (
            (0.02, 0.02),
            (0.02, 0.01),
            (0.02, 600.1),
            (0.02, True),
            (0.02, math.nan),
            (0.02, math.inf),
        )

        for time_step, max_time in invalid_cases:
            with self.subTest(
                time_step_s=time_step,
                max_time_s=max_time,
            ):
                parameters = replace(
                    self._valid_parameters(),
                    time_step_s=time_step,
                    max_time_s=cast(float, max_time),
                )
                with self.assertRaises(TankSimulationValidationError):
                    validate_tank_parameters(parameters)

    def test_valid_boundary_values_pass_validation(self) -> None:
        boundary_cases = (
            {"initial_speed_m_s": 1.0},
            {"initial_speed_m_s": 500.0},
            {"launch_angle_deg": 0.0},
            {"launch_angle_deg": 85.0},
            {"target_distance_m": 1.0},
            {"target_distance_m": 10000.0},
            {"wind_speed_m_s": -100.0},
            {"wind_speed_m_s": 100.0},
            {"linear_drag_coefficient": 0.0},
            {"linear_drag_coefficient": 2.0},
            {"hit_radius_m": 0.1},
            {"hit_radius_m": 500.0},
            {"gravity_m_s2": 50.0},
            {"time_step_s": 0.001},
            {"time_step_s": 0.1},
            {"max_time_s": 600.0},
        )

        for changes in boundary_cases:
            with self.subTest(**changes):
                parameters = replace(
                    self._valid_parameters(),
                    **changes,
                )
                validate_tank_parameters(parameters)

    def test_physics_validation_error_is_wrapped_and_chained(self) -> None:
        physics_error = PhysicsValidationError("Fizik hatası")

        with patch(
            "app.simulations.tank_simulation.simulate_projectile",
            side_effect=physics_error,
        ):
            with self.assertRaises(
                TankSimulationValidationError
            ) as context:
                simulate_tank_shot(self._valid_parameters())

        self.assertIsInstance(
            context.exception.__cause__,
            PhysicsValidationError,
        )

    def test_landed_trajectory_without_points_raises_validation_error(
        self,
    ) -> None:
        trajectory = SimulationResult(
            points=(),
            flight_time_s=1.0,
            horizontal_range_m=100.0,
            maximum_height_m=20.0,
            impact_speed_m_s=30.0,
            landed=True,
            termination_reason="ground_impact",
        )

        with patch(
            "app.simulations.tank_simulation.simulate_projectile",
            return_value=trajectory,
        ):
            with self.assertRaises(TankSimulationValidationError):
                simulate_tank_shot(self._valid_parameters())

    def test_nonfinite_impact_positions_raise_validation_error(self) -> None:
        for invalid_x in (math.inf, math.nan):
            with self.subTest(x_m=invalid_x):
                point = TrajectoryPoint(
                    time_s=1.0,
                    x_m=invalid_x,
                    y_m=0.0,
                    velocity_x_m_s=10.0,
                    velocity_y_m_s=-10.0,
                    speed_m_s=math.hypot(10.0, -10.0),
                )
                trajectory = SimulationResult(
                    points=(point,),
                    flight_time_s=1.0,
                    horizontal_range_m=invalid_x,
                    maximum_height_m=10.0,
                    impact_speed_m_s=point.speed_m_s,
                    landed=True,
                    termination_reason="ground_impact",
                )

                with patch(
                    "app.simulations.tank_simulation.simulate_projectile",
                    return_value=trajectory,
                ):
                    with self.assertRaises(
                        TankSimulationValidationError
                    ):
                        simulate_tank_shot(self._valid_parameters())


if __name__ == "__main__":
    unittest.main()