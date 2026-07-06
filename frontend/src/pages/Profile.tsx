import React, { useEffect, useMemo, useState } from "react";
import ProfileForm from "../components/Preferences";
import SeoHead from "../components/SeoHead";
import {
  EXPERIENCE_LABELS,
  HORIZON_LABELS,
  MARKET_LABELS,
  RISK_LABELS,
  SECTOR_LABELS,
} from "../constants/dicts";
import { getProfile, updateProfile, ProfileData, ProfileUpdatePayload } from "../api/profile";

export default function Profile() {
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [draft, setDraft] = useState<ProfileUpdatePayload>({
    investment_horizon: null,
    experience_level: null,
    risk_level: null,
    tickers: [],
    sectors: [],
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<"idle" | "saved" | "error">("idle");

  useEffect(() => {
    const load = async () => {
      try {
        const data = await getProfile();
        setProfile(data);
        setDraft(profileToDraft(data));
      } catch (err) {
        console.error("Ошибка загрузки профиля", err);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const handleDraftChange = (next: Partial<ProfileUpdatePayload>) => {
    setSaveStatus("idle");
    setDraft((prev) => ({ ...prev, ...next }));
  };

  const handleSave = async (payload: ProfileUpdatePayload) => {
    try {
      setSaving(true);
      setSaveStatus("idle");
      const updated = await updateProfile(payload);
      setProfile(updated);
      setDraft(profileToDraft(updated));
      setSaveStatus("saved");
      return true;
    } catch (err) {
      console.error("Ошибка сохранения профиля", err);
      setSaveStatus("error");
      return false;
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6 text-slate-600 shadow-sm">
        Загрузка профиля...
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="rounded-lg border border-red-100 bg-red-50 p-6 text-red-700">
        Не удалось загрузить профиль
      </div>
    );
  }

  const displayProfile = mergeProfile(profile, draft);

  return (
    <>
      <SeoHead
        title="Профиль | FinPulse"
        description="Закрытый раздел с настройками инвестиционного профиля."
        canonicalPath="/profile"
        noindex
      />

      <div className="space-y-6">
        <ProfileHeader profile={displayProfile} />

        <div className="grid gap-6 xl:grid-cols-[minmax(0,0.95fr)_minmax(460px,1.05fr)]">
          <ProfileSnapshot profile={displayProfile} />
          <ProfileForm
            investment_horizon={draft.investment_horizon ?? null}
            experience_level={draft.experience_level ?? null}
            risk_level={draft.risk_level ?? null}
            tickers={draft.tickers ?? []}
            sectors={draft.sectors ?? []}
            saving={saving}
            saveStatus={saveStatus}
            onChange={handleDraftChange}
            onSave={handleSave}
          />
        </div>
      </div>
    </>
  );
}

function profileToDraft(profile: ProfileData): ProfileUpdatePayload {
  return {
    investment_horizon: profile.investment_horizon ?? null,
    experience_level: profile.experience_level ?? null,
    risk_level: profile.risk_level ?? null,
    tickers: profile.tickers ?? [],
    sectors: profile.sectors ?? [],
  };
}

function mergeProfile(profile: ProfileData, draft: ProfileUpdatePayload): ProfileData {
  return {
    ...profile,
    investment_horizon: draft.investment_horizon ?? null,
    experience_level: draft.experience_level ?? null,
    risk_level: draft.risk_level ?? null,
    tickers: draft.tickers ?? [],
    sectors: draft.sectors ?? [],
  };
}

function ProfileHeader({ profile }: { profile: ProfileData }) {
  const initials = getInitials(profile.name || profile.email);

  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="bg-slate-950 px-5 py-5 text-white sm:px-6">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-md border border-white/10 bg-white/10 text-xl font-bold text-white">
            {initials}
          </div>
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-200">
              Личный кабинет
            </p>
            <h1 className="mt-1 text-2xl font-semibold">{profile.name}</h1>
            <p className="mt-1 text-sm text-slate-300">{profile.email}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Metric label="Рынок" value={MARKET_LABELS[profile.market] ?? profile.market} />
          <Metric label="Тикеры" value={String((profile.tickers ?? []).length)} />
          <Metric label="Сектора" value={String((profile.sectors ?? []).length)} />
          <Metric label="Готовность" value={`${getCompleteness(profile)}%`} />
        </div>
      </div>
      </div>
    </section>
  );
}

function ProfileSnapshot({ profile }: { profile: ProfileData }) {
  const selectedSectors = profile.sectors ?? [];
  const selectedTickers = profile.tickers ?? [];
  const profileItems = [
    profile.investment_horizon
      ? HORIZON_LABELS[profile.investment_horizon] ?? profile.investment_horizon
      : null,
    profile.experience_level
      ? EXPERIENCE_LABELS[profile.experience_level] ?? profile.experience_level
      : null,
    profile.risk_level ? RISK_LABELS[profile.risk_level] ?? profile.risk_level : null,
  ].filter(Boolean) as string[];

  const focusLine = useMemo(() => {
    if (selectedTickers.length && selectedSectors.length) {
      return `${selectedTickers.slice(0, 3).join(", ")} · ${selectedSectors
        .slice(0, 2)
        .map((sector) => SECTOR_LABELS[sector] ?? sector)
        .join(", ")}`;
    }
    if (selectedTickers.length) return selectedTickers.slice(0, 4).join(", ");
    if (selectedSectors.length) {
      return selectedSectors
        .slice(0, 3)
        .map((sector) => SECTOR_LABELS[sector] ?? sector)
        .join(", ");
    }
    return "Фокус пока не задан";
  }, [selectedSectors, selectedTickers]);

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <div className="flex flex-col gap-3 border-b border-slate-100 pb-5">
        <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">Текущий фокус</p>
        <h2 className="text-2xl font-semibold leading-tight text-slate-950">{focusLine}</h2>
        <p className="text-sm leading-relaxed text-slate-500">
          Настройки ленты сохранены по умолчанию. Их можно изменить в блоке настроек и применить кнопкой «Сохранить изменения».
        </p>
      </div>

      <div className="space-y-6 pt-5">
        <SummarySection title="Профиль">
          {profileItems.length > 0 ? (
            <ChipList items={profileItems} tone="blue" />
          ) : (
            <EmptyText>Параметры не выбраны</EmptyText>
          )}
        </SummarySection>

        <SummarySection title="Интересующие акции">
          {selectedTickers.length > 0 ? (
            <ChipList items={selectedTickers} tone="dark" />
          ) : (
            <EmptyText>Тикеры не указаны</EmptyText>
          )}
        </SummarySection>

        <SummarySection title="Интересующие сектора">
          {selectedSectors.length > 0 ? (
            <ChipList
              items={selectedSectors.map((sector) => SECTOR_LABELS[sector] ?? sector)}
              tone="gray"
            />
          ) : (
            <EmptyText>Сектора не выбраны</EmptyText>
          )}
        </SummarySection>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-28 rounded-md border border-white/10 bg-white/10 px-3 py-2">
      <p className="text-xs font-medium text-slate-300">{label}</p>
      <p className="mt-1 truncate text-sm font-semibold text-white">{value}</p>
    </div>
  );
}

function SummarySection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">{title}</h3>
      {children}
    </div>
  );
}

function ChipList({ items, tone }: { items: string[]; tone: "blue" | "dark" | "gray" }) {
  const toneClass = {
    blue: "border-blue-200 bg-blue-50 text-blue-700",
    dark: "border-slate-800 bg-slate-950 text-white",
    gray: "border-slate-200 bg-slate-50 text-slate-700",
  }[tone];

  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <span key={item} className={`rounded-full border px-3 py-1.5 text-sm font-medium ${toneClass}`}>
          {item}
        </span>
      ))}
    </div>
  );
}

function EmptyText({ children }: { children: React.ReactNode }) {
  return <p className="text-sm text-gray-500">{children}</p>;
}

function getInitials(value: string) {
  const clean = value.trim();
  if (!clean) return "FP";
  const parts = clean.split(/\s+/).filter(Boolean);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return clean.slice(0, 2).toUpperCase();
}

function getCompleteness(profile: ProfileData) {
  const checks = [
    Boolean(profile.investment_horizon),
    Boolean(profile.experience_level),
    Boolean(profile.risk_level),
    (profile.tickers ?? []).length > 0,
    (profile.sectors ?? []).length > 0,
  ];
  return Math.round((checks.filter(Boolean).length / checks.length) * 100);
}
