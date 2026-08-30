export interface HospitalResource {
  name: string;
  available: number;
  total: number;
  unit: string;
}

export const hospitalResources: HospitalResource[] = [
  {
    name: "ICU Beds",
    available: 4,
    total: 12,
    unit: "beds",
  },
  {
    name: "General Beds",
    available: 42,
    total: 80,
    unit: "beds",
  },
  {
    name: "Ventilators",
    available: 2,
    total: 8,
    unit: "units",
  },
  {
    name: "Monitors",
    available: 18,
    total: 25,
    unit: "units",
  },
];