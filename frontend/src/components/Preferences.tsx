import {
  EXPERIENCE_LABELS,
  HORIZON_LABELS,
  RISK_LABELS,
  SECTOR_LABELS,
} from "../constants/dicts";
import { useState } from "react";
import type {
  ExperienceLevel,
  InvestmentHorizon,
  ProfileUpdatePayload,
  RiskLevel,
} from "../api/profile";

type ProfileFormProps = {
  investment_horizon: InvestmentHorizon | null;
  experience_level: ExperienceLevel | null;
  risk_level: RiskLevel | null;
  tickers: string[];
  sectors: string[];
  saving?: boolean;
  saveStatus?: "idle" | "saved" | "error";
  onChange: (next: Partial<ProfileUpdatePayload>) => void;
  onSave: (payload: ProfileUpdatePayload) => boolean | Promise<boolean>;
};

type SegmentOption<T extends string> = {
  value: T;
  label: string;
  note: string;
};

const HORIZON_OPTIONS: SegmentOption<InvestmentHorizon>[] = [
  { value: "short", label: HORIZON_LABELS.short, note: "Дни-недели" },
  { value: "mid", label: HORIZON_LABELS.mid, note: "Месяцы" },
  { value: "long", label: HORIZON_LABELS.long, note: "Годы" },
];

const EXPERIENCE_OPTIONS: SegmentOption<ExperienceLevel>[] = [
  { value: "beginner", label: EXPERIENCE_LABELS.beginner, note: "Больше простоты" },
  { value: "intermediate", label: EXPERIENCE_LABELS.intermediate, note: "Баланс деталей" },
  { value: "pro", label: EXPERIENCE_LABELS.pro, note: "Больше контекста" },
];

const RISK_OPTIONS: SegmentOption<RiskLevel>[] = [
  { value: "low", label: RISK_LABELS.low, note: "Осторожно" },
  { value: "medium", label: RISK_LABELS.medium, note: "Сбалансированно" },
  { value: "high", label: RISK_LABELS.high, note: "Агрессивнее" },
];

const POPULAR_TICKERS = ["SBER", "GAZP", "LKOH", "YDEX", "TATN", "NVTK", "GMKN", "VTBR"];

function normalizeTicker(input: string) {
  return input.trim().toUpperCase().replace(/[^A-Z0-9_-]/g, "");
}

export default function ProfileForm({
  investment_horizon,
  experience_level,
  risk_level,
  tickers,
  sectors,
  saving = false,
  saveStatus = "idle",
  onChange,
  onSave,
}: ProfileFormProps) {
  const [isEditing, setIsEditing] = useState(false);

  const toggleSector = (value: string) => {
    if (!isEditing || saving) return;
    onChange({
      sectors: sectors.includes(value)
        ? sectors.filter((sector) => sector !== value)
        : [...sectors, value],
    });
  };

  const addTicker = (raw: string) => {
    if (!isEditing || saving) return;
    const ticker = normalizeTicker(raw);
    if (!ticker || tickers.includes(ticker)) return;
    onChange({ tickers: [...tickers, ticker] });
  };

  const removeTicker = (ticker: string) => {
    if (!isEditing || saving) return;
    onChange({ tickers: tickers.filter((current) => current !== ticker) });
  };

  const handlePrimaryAction = async () => {
    if (!isEditing) {
      setIsEditing(true);
      return;
    }

    const saved = await onSave({
      investment_horizon,
      experience_level,
      risk_level,
      tickers,
      sectors,
    });

    if (saved) {
      setIsEditing(false);
    }
  };

  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 bg-slate-950 px-5 py-4 text-white sm:px-6">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-blue-200">
              Настройки ленты
            </p>
            <h2 className="mt-1 text-2xl font-semibold">Профиль FinPulse</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-300">
              Настройки ленты уже сохранены по умолчанию. Чтобы изменить их, сначала нажмите «Изменить».
            </p>
          </div>
          <SaveState saving={saving} status={saveStatus} isEditing={isEditing} />
        </div>
      </div>

      <div className="space-y-7 px-5 py-5 sm:px-6">
        <SegmentGroup
          title="Горизонт"
          value={investment_horizon}
          options={HORIZON_OPTIONS}
          onSelect={(value) => onChange({ investment_horizon: value })}
          disabled={!isEditing || saving}
        />

        <SegmentGroup
          title="Опыт"
          value={experience_level}
          options={EXPERIENCE_OPTIONS}
          onSelect={(value) => onChange({ experience_level: value })}
          disabled={!isEditing || saving}
        />

        <SegmentGroup
          title="Риск"
          value={risk_level}
          options={RISK_OPTIONS}
          onSelect={(value) => onChange({ risk_level: value })}
          disabled={!isEditing || saving}
        />

        <div>
          <div className="mb-3 flex items-center justify-between gap-3">
            <h3 className="font-semibold text-slate-950">Тикеры</h3>
            <span className="text-sm text-slate-500">{tickers.length}</span>
          </div>
          <TickerInput onAdd={addTicker} disabled={!isEditing || saving} />
          <div className="mt-3 flex flex-wrap gap-2">
            {tickers.map((ticker) => (
              <button
                key={ticker}
                type="button"
                disabled={!isEditing || saving}
                className="inline-flex h-9 items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-3 text-sm font-semibold text-blue-700 transition hover:border-blue-300 hover:bg-blue-100 disabled:cursor-not-allowed disabled:border-slate-200 disabled:bg-slate-50 disabled:text-slate-400"
                onClick={() => removeTicker(ticker)}
                aria-label={`Удалить ${ticker}`}
              >
                {ticker}
                <span className="text-blue-500">×</span>
              </button>
            ))}
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {POPULAR_TICKERS.filter((ticker) => !tickers.includes(ticker)).map((ticker) => (
              <button
                key={ticker}
                type="button"
                disabled={!isEditing || saving}
                className="h-8 rounded-full border border-slate-200 px-3 text-sm font-medium text-slate-600 transition hover:border-blue-300 hover:text-blue-700 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-300"
                onClick={() => addTicker(ticker)}
              >
                + {ticker}
              </button>
            ))}
          </div>
        </div>

        <div>
          <div className="mb-3 flex items-center justify-between gap-3">
            <h3 className="font-semibold text-slate-950">Сектора</h3>
            <span className="text-sm text-slate-500">{sectors.length}</span>
          </div>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {Object.entries(SECTOR_LABELS).map(([key, label]) => {
              const selected = sectors.includes(key);
              return (
                <button
                  key={key}
                  type="button"
                  disabled={!isEditing || saving}
                  className={`min-h-11 rounded-md border px-3 py-2 text-left text-sm font-medium transition ${
                    selected
                      ? "border-blue-500 bg-blue-50 text-blue-700 shadow-sm"
                      : "border-slate-200 bg-white text-slate-700 hover:border-blue-200 hover:bg-slate-50"
                  } disabled:cursor-not-allowed disabled:opacity-70`}
                  onClick={() => toggleSector(key)}
                  aria-pressed={selected}
                >
                  <span className="flex items-center justify-between gap-3">
                    <span>{label}</span>
                    <span
                      className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-xs ${
                        selected ? "border-blue-500 bg-blue-600 text-white" : "border-slate-300 text-transparent"
                      }`}
                    >
                      ✓
                    </span>
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className="grid gap-3 border-t border-slate-100 px-5 py-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center sm:px-6">
        <p className="min-w-0 text-sm leading-relaxed text-slate-500">
          По умолчанию: Россия · MOEX · публичная лента
        </p>
        <button
          type="button"
          disabled={saving}
          onClick={() => void handlePrimaryAction()}
          className="h-11 w-full rounded-md bg-blue-600 px-5 text-sm font-semibold leading-none text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300 sm:w-auto sm:min-w-48"
        >
          {saving ? "Сохраняем..." : isEditing ? "Сохранить изменения" : "Изменить"}
        </button>
      </div>
    </section>
  );
}

function SegmentGroup<T extends string>({
  title,
  value,
  options,
  onSelect,
  disabled = false,
}: {
  title: string;
  value: T | null;
  options: SegmentOption<T>[];
  onSelect: (value: T) => void;
  disabled?: boolean;
}) {
  return (
    <div>
      <h3 className="mb-3 font-semibold text-slate-950">{title}</h3>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
        {options.map((option) => {
          const selected = value === option.value;
          return (
            <button
              key={option.value}
              type="button"
              className={`min-h-20 rounded-md border p-3 text-left transition ${
                selected
                  ? "border-blue-500 bg-blue-50 text-blue-700 shadow-sm"
                  : "border-slate-200 bg-white text-slate-700 hover:border-blue-200 hover:bg-slate-50"
              } disabled:cursor-not-allowed disabled:opacity-70`}
              disabled={disabled}
              onClick={() => onSelect(option.value)}
              aria-pressed={selected}
            >
              <span className="block text-sm font-semibold leading-snug">{option.label}</span>
              <span className={`mt-1 block text-xs ${selected ? "text-blue-600" : "text-slate-500"}`}>
                {option.note}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function TickerInput({ onAdd, disabled = false }: { onAdd: (ticker: string) => void; disabled?: boolean }) {
  return (
    <input
      className="h-11 w-full rounded-md border border-slate-200 px-3 text-base outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-400"
      placeholder="SBER, GAZP, LKOH"
      disabled={disabled}
      onKeyDown={(event) => {
        if (event.key === "Enter") {
          event.preventDefault();
          const input = event.currentTarget;
          onAdd(input.value);
          input.value = "";
        }
      }}
      onBlur={(event) => {
        const input = event.currentTarget;
        if (!input.value.trim()) return;
        onAdd(input.value);
        input.value = "";
      }}
    />
  );
}

function SaveState({
  saving,
  status,
  isEditing,
}: {
  saving: boolean;
  status: "idle" | "saved" | "error";
  isEditing: boolean;
}) {
  if (saving) {
    return <span className="text-sm font-medium text-blue-200">Сохраняем...</span>;
  }

  if (status === "saved") {
    return <span className="text-sm font-medium text-green-200">Сохранено</span>;
  }

  if (status === "error") {
    return <span className="text-sm font-medium text-red-200">Не удалось сохранить</span>;
  }

  if (isEditing) {
    return <span className="text-sm font-medium text-blue-200">Редактирование</span>;
  }

  return <span className="text-sm font-medium text-slate-300">По умолчанию сохранено</span>;
}
