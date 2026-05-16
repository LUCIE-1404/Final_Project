# Workflow Do An: AI Lecture Assistant + ML Core

## Muc tieu

Xay dung ung dung ho tro phan tich bai giang audio. Phan giao dien co the dung Streamlit, phan machine learning core phai tu train model bang Python thuan, khong dung framework ML de train.

## Huong da chon

Them model phan loai chu de bai giang tu transcript:

```text
Audio -> Gemini transcript -> ML model tu train -> topic du doan -> summary/quiz/export
```

Model ML core:

- Bai toan: text classification.
- Input: transcript/noi dung bai giang.
- Output: chu de bai giang.
- Thuat toan chinh: Multinomial Naive Bayes tu cai dat.
- Thuat toan so sanh: K-Nearest Neighbor tu cai dat.
- Bieu dien text: Bag of Words + bigram.
- Dataset: `dataset/lecture_dataset.csv` va `dataset/lecture_dataset_extra.csv`.
- Model luu tai: `models/lecture_topic_classifier.json`.

## Label dataset

Dataset ban dau gom 5 nhom:

- `python`
- `machine_learning`
- `database`
- `web`
- `math`

## Tien do

- [x] Chon huong giai quyet phu hop mon Python + ML co ban.
- [x] Xac dinh yeu cau: train model bang Python thuan, co the dung Streamlit lam web.
- [x] Tao dataset mau cho bai toan phan loai bai giang.
- [x] Cai dat preprocessing bang Python thuan.
- [x] Them bigram feature de hoc cac cum tu nhu `linear_regression`, `primary_key`, `basic_calculus`.
- [x] Cai dat Multinomial Naive Bayes bang Python thuan.
- [x] Cai dat K-Nearest Neighbor bang Python thuan de so sanh model.
- [x] Viet script train/evaluate/save model.
- [x] Tich hop model vao app Streamlit.
- [x] Chay kiem tra core workflow.

## Cach chay du kien

Train model:

```powershell
.\venv\Scripts\python.exe -m ml_core.train_model
```

Chay app:

```powershell
.\venv\Scripts\streamlit.exe run app.py
```

## Tieu chi hoan thanh core

- Train duoc model tu CSV.
- In ra accuracy va confusion matrix.
- Luu model ra file JSON.
- Load model de predict transcript moi.
- App hien thi chu de du doan va confidence.

## Ket qua kiem tra hien tai

- Dataset size: 250 mau.
- Train/test split: 200/50.
- Selected model: `naive_bayes`.
- Naive Bayes alpha smoothing: 0.5.
- Accuracy hien tai cua model chon: 88.00%.
- KNN comparison: `k=3` dat 76.00%, `k=5` dat 80.00%, `k=7` dat 80.00%.
- Unit test: 6 tests OK.
- Syntax check: OK.

## Cai tien da lam de tang accuracy

- Mo rong dataset tu 125 len 250 mau, can bang 5 label.
- Them du lieu tieng Anh de hop voi audio bai giang tieng Anh.
- Them bigram feature de model nhan ra cum tu 2 tu.
- Tinh lai Laplace smoothing voi `alpha = 0.5`.
- Them KNN voi cosine similarity de so sanh voi Naive Bayes.
- App hien thi `ML model evaluation` gom selected model, accuracy, dataset size va bang comparison.
