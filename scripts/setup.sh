#!/bin/bash
##
## Setup completo: Download dataset + Treinar modelo
## Uso: ./scripts/setup.sh
##

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "================================================"
echo "Credit Risk Setup - Download + Training"
echo "================================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Ativar venv
if [ ! -d "venv" ]; then
    echo -e "${RED} venv não encontrado. Crie com: python -m venv venv${NC}"
    exit 1
fi

echo -e "${YELLOW}Ativando ambiente virtual...${NC}"
source venv/bin/activate

# 1. Verificar credenciais Kaggle
echo -e "\n${YELLOW}[1/4] Verificando credenciais Kaggle...${NC}"
if [ ! -f ~/.kaggle/kaggle.json ]; then
    echo -e "${RED} Credenciais Kaggle não encontradas${NC}"
    echo ""
    echo "Configure:"
    echo "1. https://www.kaggle.com/settings/account"
    echo "2. Create New Token -> Download kaggle.json"
    echo "3. mv ~/Downloads/kaggle.json ~/.kaggle/"
    echo "4. chmod 600 ~/.kaggle/kaggle.json"
    exit 1
fi
chmod 600 ~/.kaggle/kaggle.json
echo -e "${GREEN} Credenciais OK${NC}"

# 2. Download dataset
echo -e "\n${YELLOW}[2/4] Baixando dataset...${NC}"
mkdir -p data/credit_card_approval
cd data/credit_card_approval

if [ -f "application_record.csv" ] && [ -f "credit_record.csv" ]; then
    echo -e "${GREEN} Dataset já existe${NC}"
else
    kaggle datasets download -d rikdifos/credit-card-approval-prediction
    unzip -o credit-card-approval-prediction.zip
    /bin/rm credit-card-approval-prediction.zip
    echo -e "${GREEN} Download completo${NC}"
fi
cd "$PROJECT_ROOT"

# 3. Instalar dependências
echo -e "\n${YELLOW}[3/4] Instalando dependências ML...${NC}"
pip install -q xgboost scikit-learn pandas shap joblib
echo -e "${GREEN} Dependências instaladas${NC}"

# 4. Treinar modelo
echo -e "\n${YELLOW}[4/4] Treinando modelo...${NC}"
python -m app.projects.creditrisk.services.model_training

if [ -f "data/models/credit_risk_xgboost.pkl" ]; then
    echo ""
    echo "================================================"
    echo -e "${GREEN} Setup completo!${NC}"
    echo "================================================"
    echo ""
    echo "Próximos passos:"
    echo "  uvicorn app.main:app --reload"
    echo "  http://localhost:8000/credit-risk/"
else
    echo -e "${RED} Erro no treinamento${NC}"
    exit 1
fi
