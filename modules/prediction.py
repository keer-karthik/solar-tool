import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from datetime import date


def build_features(monthly_df, weather_df):
    weather_monthly = weather_df.groupby(["year", "month"]).agg(
        monthly_cdd=("cdd", "sum"), avg_temp=("temp_mean", "mean")
    ).reset_index()

    feat = monthly_df.merge(weather_monthly, on=["year", "month"], how="left")
    feat["month_sin"] = np.sin(2 * np.pi * feat["month"] / 12)
    feat["month_cos"] = np.cos(2 * np.pi * feat["month"] / 12)
    feat = feat.sort_values("year_month").reset_index(drop=True)
    feat["trend"] = range(len(feat))
    return feat


FEATURE_COLS = ["monthly_cdd", "month_sin", "month_cos", "trend"]


def train_model(features_df):
    X = features_df[FEATURE_COLS].values
    y = features_df["units"].values

    model = Ridge(alpha=1.0)
    model.fit(X, y)

    y_pred = model.predict(X)
    metrics = {
        "r2": round(r2_score(y, y_pred), 3),
        "mae": round(mean_absolute_error(y, y_pred), 1),
        "coefficients": dict(zip(FEATURE_COLS, model.coef_.round(3))),
        "intercept": round(model.intercept_, 2),
    }

    features_df = features_df.copy()
    features_df["predicted_units"] = y_pred.round(0).astype(int)
    return model, features_df, metrics


def predict_future(model, weather_df, last_trend_index, months_ahead=12):
    avg_cdd = weather_df.groupby("month")["cdd"].sum() / weather_df["year"].nunique()
    avg_monthly_cdd = avg_cdd.to_dict()

    current = date.today()
    rows = []
    for i in range(1, months_ahead + 1):
        m = (current.month - 1 + i) % 12 + 1
        y = current.year + (current.month - 1 + i) // 12
        cdd = avg_monthly_cdd.get(m, 0)

        X = np.array([[cdd, np.sin(2 * np.pi * m / 12),
                        np.cos(2 * np.pi * m / 12), last_trend_index + i]])
        pred = max(0, round(model.predict(X)[0]))

        rows.append({"year_month": f"{y}-{m:02d}", "year": y, "month": m,
                      "monthly_cdd": round(cdd, 1), "predicted_units": pred})

    return pd.DataFrame(rows)
