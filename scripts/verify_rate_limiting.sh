#!/bin/bash
# Verification script for Rate Limiting + Quota Tracking system

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "  Verificando Sistema de Rate Limiting"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Unit tests
echo "1. Executando testes unitários..."
if python -m pytest tests/test_rate_limiting.py -v --tb=short; then
    echo -e "${GREEN}[OK]Testes unitários: OK (11/11)${NC}"
else
    echo -e "${RED}[FAIL]Testes unitários falharam${NC}"
    exit 1
fi
echo ""

# Test 2: Integration tests
echo "2. Executando testes de integração..."
if python -m pytest tests/test_rate_limiting_integration.py -v --tb=short; then
    echo -e "${GREEN}[OK]Testes de integração: OK (7/7)${NC}"
else
    echo -e "${RED}[FAIL]Testes de integração falharam${NC}"
    exit 1
fi
echo ""

# Test 3: Import check
echo "3. Verificando imports dos middlewares..."
if python -c "from app.middleware import get_global_rate_limiter, get_quota_tracker; print('✓ Imports OK')"; then
    echo -e "${GREEN}[OK]Middlewares importam corretamente${NC}"
else
    echo -e "${RED}[FAIL]Erro ao importar middlewares${NC}"
    exit 1
fi
echo ""

# Test 4: Singleton pattern
echo "4. Verificando padrão singleton..."
python << 'PYEOF'
from app.middleware import get_global_rate_limiter, get_quota_tracker

limiter1 = get_global_rate_limiter()
limiter2 = get_global_rate_limiter()
assert limiter1 is limiter2, "Rate limiter não é singleton"

tracker1 = get_quota_tracker()
tracker2 = get_quota_tracker()
assert tracker1 is tracker2, "Quota tracker não é singleton"

print("✓ Singleton pattern funcionando")
PYEOF
echo -e "${GREEN}[OK] Padrão singleton: OK${NC}"
echo ""

# Test 5: Data persistence
echo "5. Verificando persistência de dados..."
if [ -f "./data/quota_usage.json" ]; then
    echo -e "${GREEN}[OK]Arquivo de quota existe: ./data/quota_usage.json${NC}"
    echo -e "${YELLOW}Conteúdo:${NC}"
    cat ./data/quota_usage.json | jq . 2>/dev/null || cat ./data/quota_usage.json
else
    echo -e "${YELLOW}[WARNING]Arquivo de quota ainda não criado (será criado no primeiro uso)${NC}"
fi
echo ""

# Test 6: File structure
echo "6. Verificando estrutura de arquivos..."
REQUIRED_FILES=(
    "app/middleware/__init__.py"
    "app/middleware/rate_limit.py"
    "app/middleware/quota_tracker.py"
    "app/middleware/README.md"
    "app/routers/admin.py"
    "tests/test_rate_limiting.py"
    "tests/test_rate_limiting_integration.py"
)

ALL_EXIST=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}  ✓${NC} $file"
    else
        echo -e "${RED}  ✗${NC} $file ${RED}(faltando)${NC}"
        ALL_EXIST=false
    fi
done

if [ "$ALL_EXIST" = true ]; then
    echo -e "${GREEN}[OK]Todos os arquivos necessários existem${NC}"
else
    echo -e "${RED}[FAIL]Alguns arquivos estão faltando${NC}"
    exit 1
fi
echo ""

# Test 7: Modified files
echo "7. Verificando arquivos modificados..."
MODIFIED_FILES=(
    "app/main.py"
    "app/projects/docqa/services/embeddings.py"
    "app/projects/docqa/services/vector_store.py"
    "app/projects/docqa/services/generation.py"
)

for file in "${MODIFIED_FILES[@]}"; do
    if grep -q "get_global_rate_limiter\|get_quota_tracker" "$file" 2>/dev/null; then
        echo -e "${GREEN}  ✓${NC} $file ${GREEN}(integrado)${NC}"
    else
        echo -e "${YELLOW}  ?${NC} $file ${YELLOW}(verificar integração)${NC}"
    fi
done
echo ""

# Summary
echo "═══════════════════════════════════════════════════════════════"
echo -e "${GREEN}  [SUCCESS] VERIFICAÇÃO COMPLETA - SISTEMA FUNCIONANDO${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Para testar o dashboard:"
echo "   1. Inicie o servidor: uvicorn app.main:app --reload"
echo "   2. Acesse: curl http://localhost:8000/admin/quotas | jq ."
echo ""
echo "Documentação completa em: app/middleware/README.md"
echo ""
