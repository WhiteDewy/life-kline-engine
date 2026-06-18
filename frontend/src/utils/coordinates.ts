type CoordinateAxis = "latitude" | "longitude";
type CoordinateDirection = "N" | "S" | "E" | "W";

interface CoordinateParts {
  degrees: number;
  minutes: number;
  direction: CoordinateDirection;
}

function normalizeCoordinate(value: number) {
  return Number.isFinite(value) ? value : 0;
}

function getDirection(axis: CoordinateAxis, value: number) {
  if (axis === "longitude") {
    return value >= 0 ? "E" : "W";
  }
  return value >= 0 ? "N" : "S";
}

function splitDegreesMinutes(value: number) {
  const absolute = Math.abs(normalizeCoordinate(value));
  const totalMinutes = Math.round(absolute * 60);
  const degrees = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  return {
    degrees,
    minutes,
  };
}

function clampMinutes(value: number) {
  const normalized = Number.isFinite(value) ? Math.round(value) : 0;
  return Math.min(59, Math.max(0, normalized));
}

export function formatCoordinateLabel(value: number, axis: CoordinateAxis) {
  if (!Number.isFinite(value)) return "-";

  const { degrees, minutes } = splitDegreesMinutes(value);
  return `${degrees}\u00b0${String(minutes).padStart(2, "0")}\u2032${getDirection(axis, value)}`;
}

export function formatCoordinateSpaced(value: number, axis: CoordinateAxis) {
  if (!Number.isFinite(value)) return "-";

  const { degrees, minutes } = splitDegreesMinutes(value);
  return `${degrees} ${getDirection(axis, value)} ${String(minutes).padStart(2, "0")}`;
}

export function formatTimezoneLabel(value: number) {
  if (!Number.isFinite(value)) return "-";
  return `GMT ${value >= 0 ? "+" : "-"}${Math.abs(value).toFixed(2)}`;
}

export function splitCoordinateParts(value: number, axis: CoordinateAxis): CoordinateParts {
  const { degrees, minutes } = splitDegreesMinutes(value);
  const direction = getDirection(axis, value);
  return {
    degrees,
    minutes,
    direction,
  };
}

export function composeCoordinateValue(
  degrees: number,
  minutes: number,
  direction: CoordinateDirection,
  axis: CoordinateAxis
) {
  const normalizedDegrees = Math.max(0, Math.round(Number.isFinite(degrees) ? degrees : 0));
  const normalizedMinutes = clampMinutes(minutes);
  const sign = axis === "longitude" ? (direction === "W" ? -1 : 1) : direction === "S" ? -1 : 1;
  return sign * (normalizedDegrees + normalizedMinutes / 60);
}
