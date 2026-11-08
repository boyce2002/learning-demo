interface DemoToolbarProps {
  baseDate: string;
  selectedDate: string;
  canReset: boolean;
  isBusy: boolean;
  onDateChange: (date: string) => void;
  onReset: () => void;
}

function addDays(dateText: string, amount: number) {
  const date = new Date(`${dateText}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + amount);
  return date.toISOString().slice(0, 10);
}

export function DemoToolbar({
  baseDate,
  selectedDate,
  canReset,
  isBusy,
  onDateChange,
  onReset,
}: DemoToolbarProps) {
  const shortcuts = [
    { label: "今天", offset: 0 },
    { label: "+1 天", offset: 1 },
    { label: "+2 天", offset: 2 },
    { label: "+4 天", offset: 4 },
  ];

  return (
    <section className="demo-toolbar" aria-labelledby="demo-toolbar-title">
      <div>
        <p id="demo-toolbar-title">演示时间舱</p>
        <span>模拟日期仅用于功能演示，不代表真实学生数据。</span>
      </div>
      <div className="demo-controls">
        <div className="demo-shortcuts" aria-label="演示日期快捷选项">
          {shortcuts.map((item) => {
            const value = addDays(baseDate, item.offset);
            return (
              <button
                type="button"
                className={selectedDate === value ? "is-active" : ""}
                disabled={isBusy}
                aria-pressed={selectedDate === value}
                onClick={() => onDateChange(value)}
                key={item.label}
              >
                {item.label}
              </button>
            );
          })}
        </div>
        <label className="demo-date-input">
          <span>选择日期</span>
          <input
            type="date"
            value={selectedDate}
            disabled={isBusy}
            onChange={(event) => event.target.value && onDateChange(event.target.value)}
          />
        </label>
        {canReset && (
          <button className="demo-reset" type="button" disabled={isBusy} onClick={onReset}>
            重置我的体验记录
          </button>
        )}
      </div>
    </section>
  );
}

