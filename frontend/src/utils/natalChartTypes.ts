// 本命盘页面类型定义（与后端 /api/natal-chart/{report_id} 对齐）

export interface PlanetPosition {
  sign: string;
  sign_label?: string;
  degree: number;
  sign_raw?: string;
  house?: number;
  house_title?: string;
  dignity?: string;
  dignity_label?: string;
  retrograde?: boolean;
  longitude?: number;
}

export interface AspectRecord {
  planet1: string;
  planet1_zh?: string;
  planet2: string;
  planet2_zh?: string;
  type: string;
  type_zh: string;
  degree: string;
  orb: string;
  nature: 'supportive' | 'challenging' | 'neutral';
  description?: string;
  summary?: string;
}

export interface ReceptionRecord {
  from: string;
  from_zh?: string;
  to: string;
  to_zh?: string;
  type: 'reception' | 'mutual_reception' | 'exaltation';
  type_zh: string;
  description: string;
}

export interface ZodiacState {
  planet: string;
  planet_zh?: string;
  sign: string;
  sign_zh?: string;
  degree: string;
  state: 'domicile' | 'exaltation' | 'detriment' | 'fall' | 'peregrine';
  state_zh: string;
  meaning: string;
}

export interface FirdariaPeriod {
  start_age: number;
  end_age: number;
  lord: string;
  lord_zh: string;
  sub_lord?: string;
  sub_lord_zh?: string;
  is_node?: boolean;
  theme?: string;
}

export interface NatalChartResponse {
  status: string;
  report_id: string;
  data: {
    natal_chart: Record<string, any>;
    firdaria_periods: FirdariaPeriod[];
    receptions: ReceptionRecord[];
    is_day_chart: boolean;
    current_age: number;
  };
}