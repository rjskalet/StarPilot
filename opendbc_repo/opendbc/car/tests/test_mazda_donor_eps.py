import pytest

from opendbc.car import structs
from opendbc.car.car_helpers import interfaces
from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.mazda.values import CAR, STEER_TO_ZERO_EPS_FW, CarControllerParams, MazdaFlags, MazdaSafetyFlags


@pytest.fixture
def empty_fingerprint():
  return {i: {} for i in range(8)}


def get_params(fw_version: bytes, fingerprint):
  car_fw = [structs.CarParams.CarFw(ecu="eps", fwVersion=fw_version)]
  return interfaces[CAR.MAZDA_CX9].get_params(
    CAR.MAZDA_CX9,
    fingerprint,
    car_fw,
    alpha_long=False,
    is_release=False,
    docs=False,
    starpilot_toggles=None,
  )


@pytest.mark.parametrize("fw_version", sorted(STEER_TO_ZERO_EPS_FW))
def test_recognized_eps_firmware_enables_donor_capability(fw_version, empty_fingerprint):
  CP = get_params(fw_version, empty_fingerprint)

  assert CP.carFingerprint == CAR.MAZDA_CX9
  assert CP.flags & MazdaFlags.STEER_TO_ZERO_EPS
  assert CP.safetyConfigs[0].safetyParam & MazdaSafetyFlags.STEER_TO_ZERO_EPS
  assert CP.minSteerSpeed == 0.0
  assert CP.steerActuatorDelay == pytest.approx(0.14)
  assert CP.dashcamOnly is False
  assert CP.wheelbase == pytest.approx(2.93)
  assert CP.steerRatio == pytest.approx(17.6)


def test_unrecognized_eps_firmware_keeps_legacy_capability(empty_fingerprint):
  CP = get_params(b'UNKNOWN-3210X-A-00\x00\x00\x00\x00\x00\x00\x00', empty_fingerprint)

  assert CP.carFingerprint == CAR.MAZDA_CX9
  assert not CP.flags & MazdaFlags.STEER_TO_ZERO_EPS
  assert not CP.safetyConfigs[0].safetyParam & MazdaSafetyFlags.STEER_TO_ZERO_EPS
  assert CP.minSteerSpeed == pytest.approx(45 * CV.KPH_TO_MS)
  assert CP.steerActuatorDelay == pytest.approx(0.1)
  assert CP.dashcamOnly is True


def test_donor_controller_limits(empty_fingerprint):
  params = CarControllerParams(get_params(next(iter(STEER_TO_ZERO_EPS_FW)), empty_fingerprint))

  assert params.STEER_MAX == 1200
  assert params.STEER_DELTA_UP == 12
  assert params.STEER_DELTA_DOWN == 12
  assert params.STEER_DRIVER_MULTIPLIER == 15
  assert params.STEER_DRIVER_ALLOWANCE == 15
  assert params.STEER_MAX_LOOKUP == ([0., 14.2, 14.5], [1200, 1200, 800])
  assert params.EPS_CEILING_LOOKUP == (
    [8.0, 8.5, 9.4, 10.3, 11.2, 12.1, 13.0, 13.9, 14.5],
    [1148, 1132, 1092, 1048, 1012, 920, 808, 676, 620],
  )
