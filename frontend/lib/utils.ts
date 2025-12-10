import { ClassValue, clsx } from 'clsx';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatDeviceName(deviceId: string): string {
  return deviceId
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export function getRiskColor(level: string): string {
  switch (level) {
    case 'safe':
      return 'text-success-600 bg-success-50';
    case 'medium':
      return 'text-warning-600 bg-warning-50';
    case 'high':
      return 'text-danger-600 bg-danger-50';
    default:
      return 'text-neutral-600 bg-neutral-50';
  }
}
