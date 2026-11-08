import { copy } from "../content/copy";

interface DailyHeaderProps {
  referenceDate: string;
}

function formatDate(dateText: string): string {
  const date = new Date(`${dateText}T00:00:00+08:00`);
  return new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    month: "long",
    day: "numeric",
    weekday: "long",
  }).format(date);
}

export function DailyHeader({ referenceDate }: DailyHeaderProps) {
  return (
    <section className="daily-header" aria-labelledby="page-title">
      <div>
        <p className="overline">DAILY CURIOSITY · 每日好奇</p>
        <h1 id="page-title">{copy.heroTitle}</h1>
        <p>{copy.heroSubtitle}</p>
      </div>
      <time dateTime={referenceDate}>{formatDate(referenceDate)}</time>
    </section>
  );
}

