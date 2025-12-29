#cd到此目录下使用  streamlit run hainan_streamlit_app.py  运行 
import os
import time
from datetime import date
import pandas as pd
import streamlit as st
import altair as alt
import re

INDUSTRY_CODE = "882011.TI"
INDUSTRY_MEMBERS_DATE = "2025-12-26"
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")

def line_crosshair(
    df,
    x_field: str,
    y_field: str,
    category_field: str | None = None,
    x_type: str = "T",
    y_type: str = "Q",
    title: str | None = None,
    value_format: str = ".2f",
    multi_tooltip: bool = False,
    tooltip_title_map: dict | None = None,
):
    nearest = alt.selection_point(nearest=True, on="pointermove", fields=[x_field], empty=False)
    base = alt.Chart(df)
    enc_x = f"{x_field}:{x_type}"
    enc_y = f"{y_field}:{y_type}"
    if category_field:
        sel_series = alt.selection_point(nearest=True, on="pointermove", fields=[category_field], empty=False)
        line = base.mark_line().encode(
            x=enc_x,
            y=enc_y,
            color=f"{category_field}:N",
        ).add_params(sel_series)
        selectors = base.mark_point().encode(
            x=enc_x,
            opacity=alt.value(0),
        ).add_params(nearest)
        points = line.mark_point().encode(
            tooltip=[alt.Tooltip(enc_x),
                     alt.Tooltip(f"{category_field}:N"),
                     alt.Tooltip(enc_y, format=value_format)],
        ).transform_filter(nearest).transform_filter(sel_series)
        rules = base.mark_rule(color="#9aa0a6").encode(
            x=enc_x,
        ).transform_filter(nearest)
        hrules = base.mark_rule(color="#9aa0a6").encode(
            y=enc_y,
        ).transform_filter(nearest).transform_filter(sel_series)
        layered = alt.layer(line, selectors, points, rules, hrules)
        if multi_tooltip:
            cats = sorted(pd.Series(df[category_field]).dropna().unique().tolist())
            pivot = base.transform_pivot(category_field, value=y_field, groupby=[x_field])
            tooltips = []
            tooltips.append(alt.Tooltip(f"{x_field}:{x_type}", title="日期"))
            for c in cats:
                title = tooltip_title_map.get(c, c) if tooltip_title_map else c
                tooltips.append(alt.Tooltip(str(c), type="quantitative", title=title, format=value_format))
            rules_multi = pivot.mark_rule(color="#9aa0a6").encode(
                x=enc_x,
                tooltip=tooltips,
            ).transform_filter(nearest)
            layered = layered + rules_multi
    else:
        line = base.mark_line(color="#4e79a7").encode(
            x=enc_x,
            y=enc_y,
        )
        selectors = base.mark_point().encode(
            x=enc_x,
            opacity=alt.value(0),
        ).add_params(nearest)
        points = line.mark_point(color="#4e79a7").encode(
            tooltip=[alt.Tooltip(enc_x), alt.Tooltip(enc_y, format=value_format)],
        ).transform_filter(nearest)
        rules = base.mark_rule(color="#9aa0a6").encode(
            x=enc_x,
        ).transform_filter(nearest)
        hrules = base.mark_rule(color="#9aa0a6").encode(
            y=enc_y,
        ).transform_filter(nearest)
        layered = alt.layer(line, selectors, points, rules, hrules)
        if multi_tooltip:
            pivot = base.transform_pivot(x_field, value=y_field, groupby=[x_field])
            rules_multi = base.mark_rule(color="#9aa0a6").encode(
                x=enc_x,
                tooltip=[alt.Tooltip(enc_y, format=value_format)],
            ).transform_filter(nearest)
            layered = layered + rules_multi
    if title:
        layered = layered.properties(title=title)
    return layered

def bar_crosshair(
    df,
    x_field: str,
    y_field: str,
    color_field: str | None = None,
    x_type: str = "N",
    y_type: str = "Q",
    title: str | None = None,
    value_format: str = ".2f",
    show_labels: bool = True,
    show_multi_tooltip: bool = False,
    tooltip_title_map: dict | None = None,
):
    nearest = alt.selection_point(nearest=True, on="pointermove", fields=[x_field], empty=False)
    base = alt.Chart(df)
    enc_x = f"{x_field}:{x_type}"
    enc_y = f"{y_field}:{y_type}"
    if color_field:
        sel_cat = alt.selection_point(nearest=True, on="pointermove", fields=[color_field], empty=False)
        bars = base.mark_bar().encode(
            x=alt.X(enc_x),
            y=alt.Y(enc_y),
            color=f"{color_field}:N",
            tooltip=[alt.Tooltip(enc_x), alt.Tooltip(f"{color_field}:N"), alt.Tooltip(enc_y, format=value_format)],
        ).add_params(sel_cat)
    else:
        bars = base.mark_bar().encode(
            x=alt.X(enc_x),
            y=alt.Y(enc_y),
            tooltip=[alt.Tooltip(enc_x), alt.Tooltip(enc_y, format=value_format)],
        )
    selectors = base.mark_point().encode(
        x=enc_x,
        opacity=alt.value(0),
    ).add_params(nearest)
    layered = alt.layer(bars, selectors)
    if show_multi_tooltip and color_field:
        cats = sorted(pd.Series(df[color_field]).dropna().unique().tolist())
        pivot = base.transform_pivot(color_field, value=y_field, groupby=[x_field])
        tooltips = []
        tooltips.append(alt.Tooltip(f"{x_field}:{x_type}", title="日期"))
        for c in cats:
            title = tooltip_title_map.get(c, c) if tooltip_title_map else c
            tooltips.append(alt.Tooltip(str(c), type="quantitative", title=title, format=value_format))
        rules_multi = pivot.mark_rule(color="transparent").encode(
            x=enc_x,
            tooltip=tooltips,
        ).transform_filter(nearest)
        layered = layered + rules_multi
    if show_labels:
        labels = base.mark_text(dy=-5, color="#dfe6f1").encode(
            x=enc_x,
            y=enc_y,
            text=alt.Text(enc_y, format=value_format),
        )
        layered = layered + labels
    if title:
        layered = layered.properties(title=title)
    return layered

def code_to_jq(code: str) -> str:
    c = str(code).strip()
    if "." in c:
        return c
    c = c.zfill(6)
    ex = "XSHE" if c[0] in ["0", "2", "3"] else "XSHG"
    return f"{c}.{ex}"


@st.cache_data(show_spinner=False)
def get_industry_members(industry_code: str, on_date: str):
    try:
        p_local = os.path.join(DATA_DIR, "members_2025-12-26.csv")
        p_default = r"c:\Users\AA\Desktop\海南板块\数据获取\members_2025-12-26.csv"
        p = p_local if os.path.exists(p_local) else p_default
        df = pd.read_csv(
            p,
            dtype={"code": str},
        )
        if "code" not in df.columns or df.empty:
            return []
        codes = [code_to_jq(x) for x in df["code"].tolist()]
        return codes
    except Exception as e:
        st.error(f"读取成分股CSV失败: {e}")
        return []


@st.cache_data(show_spinner=False)
def get_index_daily(industry_code: str, start: str, end: str):
    try:
        p_local = os.path.join(DATA_DIR, "index_2025.csv")
        p_default = r"c:\Users\AA\Desktop\海南板块\数据获取\index_2025.csv"
        p = p_local if os.path.exists(p_local) else p_default
        df = pd.read_csv(
            p,
            dtype={"date": str, "avg_return": float},
        )
        if not isinstance(df, pd.DataFrame) or df.empty:
            return pd.DataFrame()
        df["date"] = pd.to_datetime(df["date"])
        s = pd.to_datetime(start)
        e = pd.to_datetime(end)
        df = df[(df["date"] >= s) & (df["date"] <= e)]
        if df.empty:
            return pd.DataFrame()
        df = df.set_index("date").sort_index()
        df["close"] = df["avg_return"]
        return df[["close", "avg_return"]]
    except Exception as e:
        st.error(f"读取指数CSV失败: {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def get_stock_daily(codes, start: str, end: str, fields=None):
    if fields is None:
        fields = ["open", "high", "low", "close", "volume", "money"]
    if isinstance(codes, str):
        codes = [codes]
    try:
        p_local = os.path.join(DATA_DIR, "prices_2025_daily.csv")
        p_default = r"c:\Users\AA\Desktop\海南板块\数据获取\prices_2025_daily.csv"
        p = p_local if os.path.exists(p_local) else p_default
        df = pd.read_csv(
            p,
            dtype={"date": str, "code": str},
        )
        if not isinstance(df, pd.DataFrame) or df.empty:
            return pd.DataFrame()
        df["date"] = pd.to_datetime(df["date"])
        try:
            if df["date"].dt.tz is not None:
                df["date"] = df["date"].dt.tz_localize(None)
        except Exception:
            pass
        s = pd.to_datetime(start)
        e = pd.to_datetime(end)
        if codes:
            codes_jq = [code_to_jq(c) for c in codes]
            df = df[df["code"].isin(codes_jq)]
        df = df[(df["date"] >= s) & (df["date"] <= e)]
        cols = ["date", "code"] + [c for c in fields if c in df.columns]
        df = df[cols]
        df = df.set_index("date").sort_index()
        return df
    except Exception as e:
        st.error(f"读取价格CSV失败: {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def get_money_flow(codes, start: str, end: str):
    if isinstance(codes, str):
        codes = [codes]
    try:
        p_local = os.path.join(DATA_DIR, "money_flow_2025_daily.csv")
        p_default = r"c:\Users\AA\Desktop\海南板块\数据获取\money_flow_2025_daily.csv"
        p = p_local if os.path.exists(p_local) else p_default
        df = pd.read_csv(
            p,
            dtype={"date": str, "code": str, "sec_code": str},
        )
        if not isinstance(df, pd.DataFrame) or df.empty:
            return pd.DataFrame()
        if "code" not in df.columns or df["code"].fillna("").eq("").all():
            if "sec_code" in df.columns:
                df["code"] = df["sec_code"]
        df["date"] = pd.to_datetime(df["date"])
        try:
            if df["date"].dt.tz is not None:
                df["date"] = df["date"].dt.tz_localize(None)
        except Exception:
            pass
        s = pd.to_datetime(start)
        e = pd.to_datetime(end)
        if codes:
            codes_jq = [code_to_jq(c) for c in codes]
            df = df[df["code"].isin(codes_jq)]
        df = df[(df["date"] >= s) & (df["date"] <= e)]
        df = df.sort_values("date")
        return df
    except Exception as e:
        st.error(f"读取资金流CSV失败: {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def get_fundamentals(codes, query_date: str):
    return pd.DataFrame()


def get_stage_ranges():
    return {}


def format_date(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def section_overview():
    st.markdown("# 海南板块上涨逻辑全景研究报告")
    st.markdown("聚焦政策、产业、资金三大主线，用数据拆解海南板块上涨逻辑、阶段特征与可持续性，覆盖基本面、技术面、预期全维度。")


def section_background(index_df: pd.DataFrame):
    st.header("一、板块指数走势")
    st.subheader("1.1 板块指数全周期走势")
    if isinstance(index_df, pd.DataFrame) and not index_df.empty:
        closes_df = index_df.reset_index().rename(columns={"index": "date"})
        chart = line_crosshair(closes_df, "date", "close", x_type="T", y_type="Q", title="1.1 板块指数全周期走势", value_format=".2f")
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("未能获取板块指数行情数据。")

def parse_policy_date(s: str):
    s = str(s)
    m_year = re.search(r"(\d{4})年", s)
    year = int(m_year.group(1)) if m_year else None
    m_impl = re.search(r"（.*?(\d{1,2})月(\d{1,2})日.*?实施.*?）", s)
    if m_impl and year:
        return pd.Timestamp(year=year, month=int(m_impl.group(1)), day=int(m_impl.group(2)))
    m_full = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", s)
    if m_full:
        return pd.Timestamp(year=int(m_full.group(1)), month=int(m_full.group(2)), day=int(m_full.group(3)))
    m_md = re.search(r"(\d{4})年(\d{1,2})月", s)
    if m_md:
        return pd.Timestamp(year=int(m_md.group(1)), month=int(m_md.group(2)), day=1)
    return pd.NaT

def get_policies():
    try:
        p_local = os.path.join(DATA_DIR, "政策.csv")
        p_default = r"c:\Users\AA\Desktop\海南板块\政策.csv"
        p = p_local if os.path.exists(p_local) else p_default
        df = pd.read_csv(p)
    except Exception:
        return pd.DataFrame()
    for col in ["政策名称", "发布时间", "一句话总结", "政策类型"]:
        if col not in df.columns:
            return pd.DataFrame()
    df["date"] = df["发布时间"].apply(parse_policy_date)
    df = df.dropna(subset=["date"])
    df["title"] = df["政策名称"].astype(str)
    df["summary"] = df["一句话总结"].fillna("").astype(str)
    df["ptype"] = df["政策类型"].astype(str)
    return df[["date", "title", "summary", "ptype"]]

def section_policy(index_df: pd.DataFrame):
    st.header("二、政策事件")
    policies = get_policies()
    if not isinstance(index_df, pd.DataFrame) or index_df.empty or policies.empty:
        st.info("指数或政策数据缺失，无法标注政策事件。")
        return
    idx = pd.to_datetime(index_df.index)
    pts = []
    for _, r in policies.iterrows():
        d = pd.Timestamp(r["date"])
        later = idx[idx >= d]
        if len(later) == 0:
            continue
        ad = later.min()
        val = float(index_df.loc[ad, "close"])
        pts.append({"date": ad, "value": val, "title": r["title"], "summary": r["summary"], "ptype": r["ptype"], "origin_date": d})
    if not pts:
        st.info("无法在指数数据中对齐政策日期。")
        return
    line_df = index_df.reset_index().rename(columns={"index": "date"})
    merged = line_df.merge(pd.DataFrame(pts), on="date", how="left")
    nearest = alt.selection_point(nearest=True, on="pointermove", fields=["date"], empty=False)
    base = alt.Chart(merged).mark_line(color="#4e79a7").encode(x="date:O", y="close:Q")
    selectors = alt.Chart(merged).mark_point().encode(x="date:O", opacity=alt.value(0)).add_params(nearest)
    v_rule = alt.Chart(merged).mark_rule(color="#9aa0a6").encode(x="date:O").transform_filter(nearest)
    h_rule = alt.Chart(merged).mark_rule(color="#9aa0a6").encode(y="close:Q").transform_filter(nearest)
    tool = alt.Chart(merged).mark_rule(color="transparent").encode(
        x="date:O",
        tooltip=[
            alt.Tooltip("date:T", title="日期"),
            alt.Tooltip("close:Q", title="收盘价", format=".2f"),
            alt.Tooltip("ptype:N", title="政策类型"),
            alt.Tooltip("title:N", title="政策名称"),
            alt.Tooltip("summary:N", title="摘要"),
            alt.Tooltip("origin_date:T", title="政策发布时间"),
        ],
    ).transform_filter(nearest)
    pt_df = pd.DataFrame(pts)
    points = alt.Chart(pt_df).mark_point(filled=True, size=60).encode(
        x="date:T",
        y="value:Q",
        color=alt.Color("ptype:N", legend=alt.Legend(title="政策类型")),
        tooltip=["title:N", "summary:N", "ptype:N", "origin_date:T", "date:T"],
    )
    st.subheader("2.1 政策事件时间标注")
    st.altair_chart((base + selectors + v_rule + h_rule + tool + points).properties(title="2.1 政策事件时间标注"), use_container_width=True)
    st.subheader("2.2 政策总结")
    policies_sorted = policies.sort_values("date")
    lines = []
    for _, r in policies_sorted.iterrows():
        d = pd.to_datetime(r["date"]).strftime("%Y-%m-%d")
        lines.append(f"- {d} [{r['ptype']}] {r['title']}：{r['summary']}")
    st.markdown("\n".join(lines))


def section_capital_flow(members, start: str, end: str):
    st.header("三、资金流向")
    if not members:
        st.info("未能获取行业成分股列表。")
        return
    flow_df = get_money_flow(members, start, end)
    if isinstance(flow_df, pd.DataFrame) and not flow_df.empty:
        if "date" in flow_df.columns:
            flow_df = flow_df.copy()
            flow_df["date"] = pd.to_datetime(flow_df["date"])
            df_group = flow_df.groupby("date").sum(numeric_only=True)
            show_cols = []
            for col in ["net_amount_main", "net_amount_xl", "net_amount_l", "net_amount_m", "net_amount_s"]:
                if col in df_group.columns:
                    show_cols.append(col)
            if show_cols:
                rename_map = {
                    "net_amount_main": "主力净额(亿)",
                    "net_amount_xl": "超大单净额(亿)",
                    "net_amount_l": "大单净额(亿)",
                    "net_amount_m": "中单净额(亿)",
                    "net_amount_s": "小单净额(亿)",
                }
                summary_rows = []
                for col in show_cols:
                    total_val = df_group[col].sum() / 10000.0
                    summary_rows.append({"type": rename_map.get(col, col), "value": round(total_val, 2)})
                if summary_rows:
                    st.subheader(f"3.1 板块资金概况（区间：{start} 至 {end}）")
                    overview_df = pd.DataFrame(summary_rows)
                    bars = bar_crosshair(overview_df, "type", "value", color_field=None, x_type="N", y_type="Q", title=f"3.1 板块资金概况（区间：{start} 至 {end}）", value_format=".2f")
                    st.altair_chart(bars, use_container_width=True)
                plot_df_daily = df_group[show_cols].copy() / 10000.0
                plot_df_daily = plot_df_daily.rename(columns={k: v for k, v in rename_map.items() if k in plot_df_daily.columns})
                st.subheader("3.2 不同资金类型按日净流入走势（亿元）")
                st.caption("主力=机构及大资金；超大单=特大单；大单/中单/小单分别代表不同成交额级别的资金净额")
                daily_reset = plot_df_daily.reset_index().rename(columns={"index": "date"})
                daily_long = daily_reset.melt(id_vars=["date"], var_name="type", value_name="value")
                daily_chart = line_crosshair(
                    daily_long,
                    "date",
                    "value",
                    category_field="type",
                    x_type="T",
                    y_type="Q",
                    title="3.2 不同资金类型按日净流入走势（亿元）",
                    value_format=".2f",
                    multi_tooltip=True,
                )
                st.altair_chart(daily_chart, use_container_width=True)
                df_group = df_group.copy()
                df_group.index = pd.to_datetime(df_group.index)
                monthly_df = df_group[show_cols].resample("M").sum() / 10000.0
                monthly_df.index = monthly_df.index.strftime("%Y-%m")
                monthly_df = monthly_df.rename(columns={k: v for k, v in rename_map.items() if k in monthly_df.columns})
                st.subheader("3.3 月度资金结构（亿元）")
                m_reset = monthly_df.reset_index()
                if "index" in m_reset.columns:
                    m_reset = m_reset.rename(columns={"index": "month"})
                if "month" not in m_reset.columns:
                    m_reset.insert(0, "month", monthly_df.index.astype(str))
                m_long = m_reset.melt(id_vars=["month"], var_name="type", value_name="value")
                m_bars = bar_crosshair(
                    m_long,
                    "month",
                    "value",
                    color_field="type",
                    x_type="N",
                    y_type="Q",
                    title="3.3 月度资金结构（亿元）",
                    value_format=".1f",
                    show_labels=False,
                    show_multi_tooltip=True,
                )
                st.altair_chart(m_bars, use_container_width=True)
    else:
        st.info("未能获取资金流向数据。")


def section_concepts(members, start: str, end: str):
    st.header("四、赛道表现对比")
    st.subheader("4.1 赛道表现对比")
    if not members:
        st.info("未能获取成分股列表。")
        return
    prices = get_stock_daily(members, start, end, fields=["close"])
    if isinstance(prices, pd.DataFrame) and not prices.empty:
        if "close" in prices.columns:
            prices_reset = prices.reset_index()
            if "index" in prices_reset.columns:
                prices_reset.rename(columns={"index": "date"}, inplace=True)
            if "date" not in prices_reset.columns and "time" in prices_reset.columns:
                prices_reset.rename(columns={"time": "date"}, inplace=True)
            if "date" in prices_reset.columns:
                prices_pivot = prices_reset.pivot_table(index="date", columns="code", values="close")
                prices_pivot = prices_pivot.sort_index()
                base = prices_pivot.iloc[0]
                ret_pct = (prices_pivot.div(base) - 1.0) * 100.0
                ret_pct = ret_pct.dropna(how="all")
                if not ret_pct.empty:
                    ret_reset = ret_pct.reset_index().rename(columns={"index": "date"})
                    ret_long = ret_reset.melt(id_vars=["date"], var_name="code", value_name="ret_pct")
                    chart = line_crosshair(ret_long, "date", "ret_pct", category_field="code", x_type="T", y_type="Q", title="4.1 赛道表现对比（区间涨跌幅）", value_format=".1f")
                    st.altair_chart(chart, use_container_width=True)
    else:
        st.info("未能获取成分股价格数据。")


def section_constituents(members, start: str, end: str):
    st.header("五、成分股分析")
    if not members:
        st.info("未能获取成分股列表。")
        return
    prices = get_stock_daily(members, start, end, fields=["close"])
    if not isinstance(prices, pd.DataFrame) or prices.empty or "close" not in prices.columns:
        st.info("未能获取成分股价格数据，无法计算收益与波动。")
        return
    prices_reset = prices.reset_index()
    if "index" in prices_reset.columns:
        prices_reset = prices_reset.rename(columns={"index": "date"})
    if "date" not in prices_reset.columns and "time" in prices_reset.columns:
        prices_reset = prices_reset.rename(columns={"time": "date"})
    if "date" not in prices_reset.columns:
        st.info("价格数据缺少日期字段，无法计算收益与波动。")
        return
    prices_pivot = prices_reset.pivot_table(index="date", columns="code", values="close")
    prices_pivot = prices_pivot.dropna(how="all")
    if prices_pivot.empty:
        st.info("成分股价格数据为空，无法计算收益与波动。")
        return
    returns = prices_pivot.pct_change().dropna(how="all")
    if returns.empty:
        st.info("成分股收益序列为空，无法计算收益与波动。")
        return
    first = prices_pivot.iloc[0]
    last = prices_pivot.iloc[-1]
    total_return = (last / first) - 1
    vol = returns.std() * (252 ** 0.5)
    summary = pd.DataFrame({"区间收益率(%)": total_return * 100, "年化波动率(%)": vol * 100})
    summary = summary.replace([pd.NA, float("inf"), float("-inf")], 0).fillna(0)
    summary_sorted = summary.sort_values("区间收益率(%)", ascending=False)
    st.subheader("5.1 成分股区间收益率前十名")
    top10 = summary_sorted.head(10)
    top_reset = top10.reset_index()
    if "index" in top_reset.columns:
        top_reset = top_reset.rename(columns={"index": "code"})
    top_reset = top_reset.rename(columns={"区间收益率(%)": "value"})
    top_reset["label"] = top_reset["value"].round(1).astype(str)
    top_chart = bar_crosshair(top_reset, "code", "value", x_type="N", y_type="Q", title="5.1 成分股区间收益率前十名", value_format=".1f")
    st.altair_chart(top_chart, use_container_width=True)


def section_technical(index_df: pd.DataFrame):
    st.header("六、技术面分析")
    if isinstance(index_df, pd.DataFrame) and not index_df.empty:
        numeric_cols = [c for c in index_df.columns if c not in ["code"]]
        df_numeric = index_df[numeric_cols]
        st.subheader("6.1 收盘价与均线走势")
        if "close" in df_numeric.columns:
            close_series = df_numeric["close"]
            ma5 = close_series.rolling(window=5).mean()
            ma20 = close_series.rolling(window=20).mean()
            tech_df = pd.DataFrame({"close": close_series, "MA5": ma5, "MA20": ma20})
            idx = pd.to_datetime(tech_df.index)
            tech_df = tech_df.assign(date=idx)
            tech_long = tech_df.melt(id_vars=["date"], var_name="series", value_name="value")
            tech_chart = line_crosshair(
                tech_long,
                "date",
                "value",
                category_field="series",
                x_type="T",
                y_type="Q",
                title="6.1 收盘价与均线走势",
                value_format=".2f",
                multi_tooltip=True,
            )
            st.altair_chart(tech_chart, use_container_width=True)
        vol_cols = [c for c in df_numeric.columns if c in ["volume", "money"]]
        if vol_cols:
            vol_df = df_numeric[vol_cols].copy()
            vol_df = vol_df.dropna(how="all")
            has_data = not vol_df.empty and vol_df.notnull().any().any() and (vol_df.abs().sum().sum() > 0)
            if has_data:
                st.subheader("6.2 成交量与成交额")
                idx = pd.to_datetime(vol_df.index)
                vol_df = vol_df.assign(date=idx)
                vol_long = vol_df.reset_index().melt(id_vars=["date"], var_name="metric", value_name="value")
                vol_chart = bar_crosshair(
                    vol_long,
                    "date",
                    "value",
                    color_field="metric",
                    x_type="T",
                    y_type="Q",
                    title="6.2 成交量与成交额",
                    value_format=".2f",
                    show_multi_tooltip=True,
                )
                st.altair_chart(vol_chart, use_container_width=True)
        try:
            idx = pd.to_datetime(index_df.index)
            start_s = idx.min().strftime("%Y-%m-%d")
            end_s = idx.max().strftime("%Y-%m-%d")
            members = get_industry_members(INDUSTRY_CODE, end_s)
            prices = get_stock_daily(members, start_s, end_s, fields=["close"])
            if isinstance(prices, pd.DataFrame) and not prices.empty and "close" in prices.columns:
                p_reset = prices.reset_index()
                if "index" in p_reset.columns:
                    p_reset = p_reset.rename(columns={"index": "date"})
                if "date" not in p_reset.columns and "time" in p_reset.columns:
                    p_reset = p_reset.rename(columns={"time": "date"})
                if "date" in p_reset.columns:
                    p_pivot = p_reset.pivot_table(index="date", columns="code", values="close")
                    ma20_all = p_pivot.rolling(window=20).mean()
                    ma50_all = p_pivot.rolling(window=50).mean()
                    ncols = max(1, p_pivot.shape[1])
                    ratio20 = (p_pivot >= ma20_all).sum(axis=1) / ncols * 100.0
                    ratio50 = (p_pivot >= ma50_all).sum(axis=1) / ncols * 100.0
                    breadth_df = pd.DataFrame(
                        {
                            "date": pd.to_datetime(ratio20.index),
                            "MA20占比(%)": ratio20.values,
                            "MA50占比(%)": ratio50.values,
                        }
                    )
                    breadth_long = breadth_df.melt(id_vars=["date"], var_name="series", value_name="value")
                    breadth_chart = line_crosshair(breadth_long, "date", "value", category_field="series", x_type="T", y_type="Q", title="6.2 站上均线占比（%）", value_format=".1f").encode(y=alt.Y("value:Q", title="占比(%)", scale=alt.Scale(domain=[0, 100])))
                    st.altair_chart(breadth_chart, use_container_width=True)
                    ret = p_pivot.pct_change().dropna(how="all")
                    if not ret.empty:
                        st.subheader("6.3 上涨家数")
                        up_count = (ret > 0).sum(axis=1)
                        adv_df = pd.DataFrame({"date": pd.to_datetime(up_count.index), "上涨家数": up_count.values})
                        adv_chart = line_crosshair(adv_df, "date", "上涨家数", x_type="T", y_type="Q", title="6.3 上涨家数", value_format="d")
                        st.altair_chart(adv_chart, use_container_width=True)
        except Exception as _e:
            pass

def section_expectation(index_df: pd.DataFrame):
    st.header("七、月度收益")
    if not isinstance(index_df, pd.DataFrame) or index_df.empty or "close" not in index_df.columns:
        st.info("未能获取指数数据，无法进行历史业绩与预期分析。")
        return
    df = index_df.copy()
    df_reset = df.reset_index()
    date_col = None
    if "index" in df_reset.columns:
        date_col = "index"
    if "time" in df_reset.columns:
        date_col = "time"
    if "date" in df_reset.columns:
        date_col = "date"
    if not date_col:
        st.info("指数数据缺少日期字段，无法进行月度收益分析。")
        return
    df_reset[date_col] = pd.to_datetime(df_reset[date_col])
    df_reset["month"] = df_reset[date_col].dt.to_period("M")
    grouped = df_reset.groupby("month")["close"]
    first = grouped.first()
    last = grouped.last()
    monthly_ret = (last / first - 1).dropna()
    if monthly_ret.empty:
        st.info("月度收益率序列为空。")
        return
    monthly_df = monthly_ret.to_frame("月度收益率(%)")
    monthly_df["月度收益率(%)"] = monthly_df["月度收益率(%)"] * 100
    monthly_df.index = monthly_df.index.astype(str)
    st.subheader("7.1 历史月度收益率（%）")
    m_reset = monthly_df.reset_index()
    if "index" in m_reset.columns:
        m_reset = m_reset.rename(columns={"index": "month"})
    m_reset = m_reset.rename(columns={"月度收益率(%)": "value"})
    m_reset["label"] = m_reset["value"].round(1).astype(str)
    m_bars = bar_crosshair(m_reset, "month", "value", x_type="N", y_type="Q", title="7.1 历史月度收益率（%）", value_format=".1f")
    st.altair_chart(m_bars, use_container_width=True)


def section_risk(index_df: pd.DataFrame):
    st.header("八、风险提示")
    if not isinstance(index_df, pd.DataFrame) or index_df.empty or "close" not in index_df.columns:
        st.info("未能获取指数数据，无法进行风险分析。")
        return
    close_series = index_df["close"].astype(float)
    returns = close_series.pct_change().dropna()
    if returns.empty:
        st.info("指数收益序列为空，无法进行风险分析。")
        return
    vol_20d = returns.rolling(window=20).std() * (252 ** 0.5)
    cum_max = close_series.cummax()
    drawdown = close_series / cum_max - 1
    risk_df = pd.DataFrame(
        {
            "收盘价": close_series,
            "20日滚动年化波动率(%)": vol_20d * 100,
            "最大回撤(%)": drawdown * 100,
        }
    )
    st.subheader("8.1 指数最大回撤曲线（%）")
    risk_line = risk_df[["最大回撤(%)"]].copy().reset_index()
    if "index" in risk_line.columns:
        risk_line = risk_line.rename(columns={"index": "date"})
    rl_chart = line_crosshair(risk_line, "date", "最大回撤(%)", x_type="T", y_type="Q", title="8.1 指数最大回撤曲线（%）", value_format=".2f")
    st.altair_chart(rl_chart, use_container_width=True)
    st.subheader("8.2 20日滚动年化波动率（%）")
    risk_vol = risk_df[["20日滚动年化波动率(%)"]].copy().reset_index()
    if "index" in risk_vol.columns:
        risk_vol = risk_vol.rename(columns={"index": "date"})
    rv_chart = line_crosshair(risk_vol, "date", "20日滚动年化波动率(%)", x_type="T", y_type="Q", title="8.2 20日滚动年化波动率（%）", value_format=".2f")
    st.altair_chart(rv_chart, use_container_width=True)


def main():
    st.set_page_config(
        page_title="海南板块上涨逻辑全景研究报告",
        layout="wide",
    )
    start_str = "2025-01-01"
    end_str = "2025-12-31"
    members = get_industry_members(INDUSTRY_CODE, end_str)
    index_df = get_index_daily(INDUSTRY_CODE, start_str, end_str)
    section_overview()
    section_background(index_df)
    section_policy(index_df)
    section_capital_flow(members, start_str, end_str)
    section_concepts(members, start_str, end_str)
    section_constituents(members, start_str, end_str)
    section_technical(index_df)
    section_expectation(index_df)
    section_risk(index_df)


if __name__ == "__main__":
    main()
