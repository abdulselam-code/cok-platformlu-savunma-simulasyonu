from __future__ import annotations

from dataclasses import FrozenInstanceError
import math
from typing import cast
import unittest

from app.core.physics_engine import (
    PhysicsValidationError,
    SimulationParameters,
    SimulationResult,
    TrajectoryPoint,
    simulate_projectile,
    validate_parameters,
)


class PhysicsEngineTests(unittest.TestCase):
    def test_standard_projectile_without_drag_matches_analytic_solution(
        self,
    ) -> None:
        speed = 100.0
        angle_deg = 45.0
        gravity = 9.81
        angle_rad = math.radians(angle_deg)

        parameters = SimulationParameters(
            initial_speed_m_s=speed,
            launch_angle_deg=angle_deg,
            gravity_m_s2=gravity,
            linear_drag_coefficient=0.0,
            wind_speed_m_s=0.0,
            time_step_s=0.02,
        )
        result = simulate_projectile(parameters)

        expected_flight_time = 2.0 * speed * math.sin(angle_rad) / gravity
        expected_range = (
            speed**2 * math.sin(2.0 * angle_rad) / gravity
        )
        expected_maximum_height = (
            speed**2 * math.sin(angle_rad) ** 2 / (2.0 * gravity)
        )

        self.assertAlmostEqual(
            result.flight_time_s,
            expected_flight_time,
            delta=0.03,
        )
        self.assertAlmostEqual(
            result.horizontal_range_m,
            expected_range,
            delta=0.5,
        )
        self.assertAlmostEqual(
            result.maximum_height_m,
            expected_maximum_height,
            delta=0.05,
        )
        self.assertTrue(result.landed)
        self.assertEqual(result.termination_reason, "ground_impact")
        self.assertIsNotNone(result.impact_speed_m_s)
        self.assertEqual(result.points[-1].y_m, 0.0)
        self.assertTrue(result.points)
        self.assertIsInstance(result.points, tuple)

    def test_horizontal_launch_from_ground_impacts_immediately(self) -> None:
        parameters = SimulationParameters(
            initial_speed_m_s=50.0,
            launch_angle_deg=0.0,
            start_y_m=0.0,
            ground_level_m=0.0,
        )

        result = simulate_projectile(parameters)

        self.assertEqual(result.flight_time_s, 0.0)
        self.assertEqual(result.horizontal_range_m, 0.0)
        self.assertEqual(len(result.points), 1)
        self.assertTrue(result.landed)
        self.assertEqual(result.termination_reason, "ground_impact")

    def test_downward_launch_from_ground_impacts_immediately(self) -> None:
        parameters = SimulationParameters(
            initial_speed_m_s=50.0,
            launch_angle_deg=-30.0,
            start_y_m=10.0,
            ground_level_m=10.0,
        )

        result = simulate_projectile(parameters)

        self.assertEqual(result.flight_time_s, 0.0)
        self.assertEqual(result.horizontal_range_m, 0.0)
        self.assertEqual(len(result.points), 1)
        self.assertTrue(result.landed)
        self.assertEqual(result.termination_reason, "ground_impact")

    def test_horizontal_launch_above_ground_lands_over_time(self) -> None:
        parameters = SimulationParameters(
            initial_speed_m_s=50.0,
            launch_angle_deg=0.0,
            start_y_m=100.0,
            ground_level_m=0.0,
        )

        result = simulate_projectile(parameters)

        self.assertTrue(result.landed)
        self.assertGreater(result.flight_time_s, 0.0)
        self.assertGreater(len(result.points), 1)
        self.assertEqual(result.points[-1].y_m, 0.0)
        self.assertEqual(result.termination_reason, "ground_impact")

    def test_simulation_stops_when_maximum_time_is_reached(self) -> None:
        parameters = SimulationParameters(
            initial_speed_m_s=10.0,
            launch_angle_deg=45.0,
            start_y_m=1000.0,
            time_step_s=0.1,
            max_time_s=0.2,
        )

        result = simulate_projectile(parameters)

        self.assertFalse(result.landed)
        self.assertEqual(result.termination_reason, "max_time_reached")
        self.assertIsNone(result.impact_speed_m_s)
        self.assertTrue(result.points)
        self.assertLessEqual(
            result.flight_time_s,
            parameters.max_time_s,
        )

    def test_wind_and_drag_produce_finite_different_range(self) -> None:
        common_values = {
            "initial_speed_m_s": 60.0,
            "launch_angle_deg": 40.0,
            "start_y_m": 20.0,
            "time_step_s": 0.02,
        }
        calm_result = simulate_projectile(
            SimulationParameters(
                **common_values,
                wind_speed_m_s=0.0,
                linear_drag_coefficient=0.0,
            )
        )
        windy_result = simulate_projectile(
            SimulationParameters(
                **common_values,
                wind_speed_m_s=25.0,
                linear_drag_coefficient=0.15,
            )
        )

        for result in (calm_result, windy_result):
            self.assertTrue(math.isfinite(result.flight_time_s))
            self.assertTrue(math.isfinite(result.horizontal_range_m))
            self.assertTrue(math.isfinite(result.maximum_height_m))
            self.assertTrue(
                all(
                    math.isfinite(value)
                    for point in result.points
                    for value in (
                        point.time_s,
                        point.x_m,
                        point.y_m,
                        point.velocity_x_m_s,
                        point.velocity_y_m_s,
                        point.speed_m_s,
                    )
                )
            )

        self.assertNotAlmostEqual(
            calm_result.horizontal_range_m,
            windy_result.horizontal_range_m,
            places=5,
        )

    def test_invalid_initial_speeds_raise_validation_error(self) -> None:
        invalid_values = (
            0.0,
            -1.0,
            2000.1,
            True,
            math.nan,
            math.inf,
            -math.inf,
        )

        for value in invalid_values:
            with self.subTest(initial_speed_m_s=value):
                parameters = SimulationParameters(
                    initial_speed_m_s=value,
                    launch_angle_deg=45.0,
                )
                with self.assertRaises(PhysicsValidationError):
                    validate_parameters(parameters)

    def test_invalid_launch_angles_raise_validation_error(self) -> None:
        invalid_values = (-89.1, 89.1, True, math.nan, math.inf)

        for value in invalid_values:
            with self.subTest(launch_angle_deg=value):
                parameters = SimulationParameters(
                    initial_speed_m_s=100.0,
                    launch_angle_deg=value,
                )
                with self.assertRaises(PhysicsValidationError):
                    validate_parameters(parameters)

    def test_start_below_ground_raises_validation_error(self) -> None:
        parameters = SimulationParameters(
            initial_speed_m_s=100.0,
            launch_angle_deg=45.0,
            start_y_m=9.9,
            ground_level_m=10.0,
        )

        with self.assertRaises(PhysicsValidationError):
            validate_parameters(parameters)

    def test_invalid_gravity_values_raise_validation_error(self) -> None:
        invalid_values = (0.0, -1.0, 50.1, True, math.nan, math.inf)

        for value in invalid_values:
            with self.subTest(gravity_m_s2=value):
                parameters = SimulationParameters(
                    initial_speed_m_s=100.0,
                    launch_angle_deg=45.0,
                    gravity_m_s2=value,
                )
                with self.assertRaises(PhysicsValidationError):
                    validate_parameters(parameters)

    def test_invalid_wind_speeds_raise_validation_error(self) -> None:
        invalid_values = (-200.1, 200.1, True, math.nan, math.inf)

        for value in invalid_values:
            with self.subTest(wind_speed_m_s=value):
                parameters = SimulationParameters(
                    initial_speed_m_s=100.0,
                    launch_angle_deg=45.0,
                    wind_speed_m_s=value,
                )
                with self.assertRaises(PhysicsValidationError):
                    validate_parameters(parameters)

    def test_invalid_drag_coefficients_raise_validation_error(self) -> None:
        invalid_values = (-0.1, 5.1, True, math.nan, math.inf)

        for value in invalid_values:
            with self.subTest(linear_drag_coefficient=value):
                parameters = SimulationParameters(
                    initial_speed_m_s=100.0,
                    launch_angle_deg=45.0,
                    linear_drag_coefficient=value,
                )
                with self.assertRaises(PhysicsValidationError):
                    validate_parameters(parameters)

    def test_invalid_time_steps_raise_validation_error(self) -> None:
        invalid_values = (0.0, 0.0009, 0.1001, True, math.nan, math.inf)

        for value in invalid_values:
            with self.subTest(time_step_s=value):
                parameters = SimulationParameters(
                    initial_speed_m_s=100.0,
                    launch_angle_deg=45.0,
                    time_step_s=value,
                )
                with self.assertRaises(PhysicsValidationError):
                    validate_parameters(parameters)

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
                parameters = SimulationParameters(
                    initial_speed_m_s=100.0,
                    launch_angle_deg=45.0,
                    time_step_s=time_step,
                    max_time_s=max_time,
                )
                with self.assertRaises(PhysicsValidationError):
                    validate_parameters(parameters)

    def test_non_parameter_object_raises_validation_error(self) -> None:
        invalid_parameters = cast(SimulationParameters, object())

        with self.assertRaises(PhysicsValidationError):
            validate_parameters(invalid_parameters)

    def test_result_contains_valid_ordered_data_structures(self) -> None:
        result = simulate_projectile(
            SimulationParameters(
                initial_speed_m_s=75.0,
                launch_angle_deg=35.0,
                start_y_m=10.0,
            )
        )

        self.assertIsInstance(result, SimulationResult)
        self.assertIsInstance(result.points, tuple)
        self.assertTrue(result.points)
        self.assertTrue(
            all(isinstance(point, TrajectoryPoint) for point in result.points)
        )

        for point in result.points:
            values = (
                point.time_s,
                point.x_m,
                point.y_m,
                point.velocity_x_m_s,
                point.velocity_y_m_s,
                point.speed_m_s,
            )
            self.assertTrue(all(math.isfinite(value) for value in values))

        times = [point.time_s for point in result.points]
        self.assertTrue(
            all(
                earlier <= later
                for earlier, later in zip(times, times[1:])
            )
        )
        self.assertEqual(result.flight_time_s, result.points[-1].time_s)

    def test_data_classes_are_immutable(self) -> None:
        parameters = SimulationParameters(
            initial_speed_m_s=100.0,
            launch_angle_deg=45.0,
        )
        point = TrajectoryPoint(
            time_s=0.0,
            x_m=0.0,
            y_m=0.0,
            velocity_x_m_s=10.0,
            velocity_y_m_s=10.0,
            speed_m_s=math.hypot(10.0, 10.0),
        )

        with self.assertRaises(FrozenInstanceError):
            setattr(parameters, "initial_speed_m_s", 200.0)

        with self.assertRaises(FrozenInstanceError):
            setattr(point, "x_m", 50.0)

    def test_horizontal_range_is_relative_to_start_x(self) -> None:
        start_x = 250.0
        result = simulate_projectile(
            SimulationParameters(
                initial_speed_m_s=80.0,
                launch_angle_deg=40.0,
                start_x_m=start_x,
            )
        )

        expected_range = result.points[-1].x_m - start_x
        self.assertAlmostEqual(
            result.horizontal_range_m,
            expected_range,
            places=12,
        )
        self.assertNotAlmostEqual(
            result.horizontal_range_m,
            result.points[-1].x_m,
            places=7,
        )

    def test_ground_impact_interpolation_ends_exactly_on_ground(self) -> None:
        ground_level = 15.0
        result = simulate_projectile(
            SimulationParameters(
                initial_speed_m_s=40.0,
                launch_angle_deg=25.0,
                start_y_m=30.0,
                ground_level_m=ground_level,
                time_step_s=0.1,
            )
        )

        self.assertTrue(result.landed)
        self.assertEqual(result.termination_reason, "ground_impact")
        self.assertEqual(result.points[-1].y_m, ground_level)
        self.assertGreaterEqual(result.points[-1].y_m, ground_level)

    def test_valid_boundary_values_pass_validation(self) -> None:
        boundary_cases = (
            {"launch_angle_deg": -89.0},
            {"launch_angle_deg": 89.0},
            {"wind_speed_m_s": -200.0},
            {"wind_speed_m_s": 200.0},
            {"linear_drag_coefficient": 0.0},
            {"linear_drag_coefficient": 5.0},
            {"time_step_s": 0.001},
            {"time_step_s": 0.1},
        )

        for overrides in boundary_cases:
            with self.subTest(**overrides):
                values = {
                    "initial_speed_m_s": 100.0,
                    "launch_angle_deg": 45.0,
                }
                values.update(overrides)
                parameters = SimulationParameters(**values)
                validate_parameters(parameters)


if __name__ == "__main__":
    unittest.main()