export interface PeriodBoundaries {
  now: Date;
  periodStart: Date;
  prevPeriodStart: Date;
}

export const getPeriodBoundaries = (periodMonths: number): PeriodBoundaries => {
  const now = new Date();
  const periodStart = new Date(now);
  periodStart.setMonth(periodStart.getMonth() - periodMonths);
  periodStart.setHours(0, 0, 0, 0);
  const prevPeriodStart = new Date(periodStart);
  prevPeriodStart.setMonth(prevPeriodStart.getMonth() - periodMonths);
  return { now, periodStart, prevPeriodStart };
};
