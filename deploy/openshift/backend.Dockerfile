FROM image-registry.openshift-image-registry.svc:5000/openshift/nodejs:20-ubi9 AS frontend-build

WORKDIR /opt/app-root/src
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build


FROM image-registry.openshift-image-registry.svc:5000/openshift/python:3.12-ubi9

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /opt/app-root/src

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

COPY backend/ ./backend/
COPY scripts/seed-demo-data.py ./scripts/seed-demo-data.py
COPY --from=frontend-build /opt/app-root/src/dist ./static

WORKDIR /opt/app-root/src/backend
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
