# Quick Start Guide - Refactored Dashboard

## 🚀 Start the Dashboard

```bash
cd ~/clinical_trials_dashboard
source .venv/bin/activate
streamlit run app.py
```

**Opens at**: http://localhost:8501

---

## 📊 What's New

### ✨ Real Data Integration
- Dashboard now loads cleaned clinical trial data from `data/processed/india_trials_clean.csv`
- No more mock data - everything is real!

### 🔍 Global Filters
Use sidebar to filter across all pages:
- **Therapeutic Area** - Select disease categories
- **Phase** - Filter by trial phase (1, 2, 3, 4)
- **Recruitment Status** - Filter by status (Recruiting, Active, etc.)
- **Sponsor** - Select specific sponsor
- **States** - Filter by Indian states
- **Year Range** - Select trial start year range

### 🎯 Dynamic KPIs
All metrics update based on filters:
- Total Active Trials
- Active Sponsors
- Recruiting Trials
- Average Duration
- Most Active Therapeutic Area

### 🔄 Data Refresh
- Click `🔄 Refresh Data` button in sidebar to reload CSV
- Manually refresh by running:
  ```bash
  python -m src.cleaning.clean_trials
  ```

### 📈 Timestamp Display
Sidebar shows:
- Last updated time
- Total records loaded
- Data file location

---

## 📋 Dashboard Pages

### 1. Overview Dashboard 📊
- Key performance indicators
- Trial distribution by therapeutic area
- Trial growth over years
- Phase and recruitment status distributions

### 2. Sponsor Intelligence 🏢
- Top sponsors by trial count
- Portfolio analysis
- Sponsor diversity metrics
- Detailed sponsor information table

### 3. Therapeutic Area Analysis 🔬
- Disease category overview
- Most active therapeutic areas
- Phase distribution per area
- Enrollment analysis by area

### 4. Geographic Analysis 🗺️
- States with trials
- Cities research centers
- Top research locations
- State-wise trial details

### 5. Trial Explorer 🔍
- Advanced search and filtering
- Multi-criteria selection
- Detailed trial information
- CSV export of results

---

## 🔧 Verify Everything Works

Run the verification suite:

```bash
cd ~/clinical_trials_dashboard
source .venv/bin/activate
python verify_refactoring.py
```

Expected output:
```
🎉 All verification tests passed!

✅ Dashboard is ready for use
```

---

## 📂 Key Files

**New/Modified**:
- `app.py` - Refactored to use real data (25 KB)
- `src/data_loader.py` - New data loading module (9.4 KB)
- `verify_refactoring.py` - Verification tests (7.5 KB)

**Documentation**:
- `REFACTORING_COMPLETE.md` - Full implementation details
- `DASHBOARD_REFACTORING.md` - Architecture documentation

**Data**:
- `data/processed/india_trials_clean.csv` - Real trial data (source)
- `logs/data_loader.log` - Data loading logs

---

## 🎯 Features Summary

| Feature | Status | Details |
|---------|--------|---------|
| Real data loading | ✅ | Loads from cleaned CSV |
| Global filters | ✅ | 6 filter types across all pages |
| Dynamic KPIs | ✅ | Update based on filters |
| Refresh button | ✅ | Manual data reload |
| Timestamp display | ✅ | Last updated + record count |
| Error handling | ✅ | User-friendly error messages |
| 5 Dashboard pages | ✅ | All pages filter-aware |
| Caching | ✅ | 1-hour TTL for performance |
| Production-ready | ✅ | Logging, validation, error handling |

---

## ❓ Troubleshooting

### Dashboard shows "Data file not found"

**Solution**: Generate the data first
```bash
# Run API ingestion
python -m src.ingestion.clinical_trials_api

# Run data cleaning
python -m src.cleaning.clean_trials

# Refresh dashboard (click 🔄 Refresh Data)
```

### Filters not working

**Solution**: Clear cache and reload
- In sidebar: Click `🔄 Refresh Data`
- In browser: Clear cache (Ctrl+Shift+Del)

### Charts appear empty

**Solution**: Check if filters eliminated all data
- Click `🔄 Reset All Filters` in sidebar
- Charts should reappear with all data

---

## 📊 Current Data Status

**Records**: 11 clinical trials
**Therapeutic Areas**: 11
**Sponsors**: 11
**States**: 10
**Date Range**: 2020-2026

To add more data:
```bash
python -m src.ingestion.clinical_trials_api
python -m src.cleaning.clean_trials
```

Then click `🔄 Refresh Data` in dashboard sidebar.

---

## 🎓 Learn More

**Documentation Files**:
- `REFACTORING_COMPLETE.md` - Implementation details
- `DASHBOARD_REFACTORING.md` - Architecture overview
- `docs/DATA_CLEANING_README.md` - Data cleaning operations
- `docs/API_INGESTION_README.md` - API ingestion details

**Code Structure**:
```
app.py (Main Streamlit app)
  ├── Imports from src/data_loader.py
  ├── Uses src/visualizations.py
  ├── References src/config.py
  └── Loads data/processed/india_trials_clean.csv
```

---

## ✅ Verification Checklist

Before using dashboard, verify:

- [ ] `data/processed/india_trials_clean.csv` exists
- [ ] Virtual environment activated
- [ ] All dependencies installed
- [ ] `python verify_refactoring.py` passes all tests
- [ ] Dashboard starts without errors

---

## 🚀 Production Deployment

When ready to deploy:

1. **Increase data**: Run full API ingestion for 100+ trials
2. **Test thoroughly**: Run `verify_refactoring.py` frequently
3. **Monitor logs**: Check `logs/data_loader.log` for issues
4. **Backup data**: Before making changes to pipeline
5. **Deploy**: Use Streamlit Cloud or similar platform

---

## 📞 Support

For questions or issues:
1. Check `logs/data_loader.log`
2. Run `verify_refactoring.py` to diagnose
3. Review error message in dashboard UI
4. Check documentation in `docs/` folder

---

**Dashboard Version**: 2.1.0
**Status**: Production Ready ✅
**Last Updated**: May 20, 2026
