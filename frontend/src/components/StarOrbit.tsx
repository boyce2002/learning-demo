import type { WeekDay, WeekStatus } from "../types";

interface StarOrbitProps {
  days: WeekDay[];
}

const statusText: Record<WeekStatus, string> = {
  done: "已点亮",
  missed: "未完成",
  today_pending: "今天待探索",
  future: "尚未到来",
};

const weekdays = ["一", "二", "三", "四", "五", "六", "日"];

function monthDay(dateText: string) {
  const [, month, day] = dateText.split("-");
  return `${Number(month)}/${Number(day)}`;
}

function fullLabel(day: WeekDay, index: number) {
  const [, month, date] = day.date.split("-");
  return `${Number(month)}月${Number(date)}日，周${weekdays[index]}，${statusText[day.status]}`;
}

export function StarOrbit({ days }: StarOrbitProps) {
  return (
    <div className="star-orbit" aria-label="本周七日星轨">
      <div className="orbit-line" aria-hidden="true" />
      {days.map((day, index) => (
        <div className={`orbit-day orbit-day--${day.status}`} key={day.date}>
          <span className="weekday">{weekdays[index]}</span>
          <span className="orbit-star" role="img" aria-label={fullLabel(day, index)}>
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="m12 2.8 2.7 5.5 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1L3.2 9.2l6.1-.9L12 2.8Z" />
            </svg>
          </span>
          <span className="orbit-date">{monthDay(day.date)}</span>
          <span className="sr-only">{statusText[day.status]}</span>
        </div>
      ))}
    </div>
  );
}

