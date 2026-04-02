#!/bin/bash
# AIDROUTE Frontend Integration Verification Script

echo "🔍 AIDROUTE Frontend Integration Verification"
echo "=============================================="
echo ""

# Check 1: Node modules installed
echo "✓ Checking dependencies..."
if [ -d "node_modules" ]; then
    echo "  ✅ node_modules directory exists"
else
    echo "  ⚠️  Run 'npm install' first"
fi

# Check 2: Key files exist
echo ""
echo "✓ Checking key files..."

files=(
    "lib/api.ts"
    "app/page.tsx"
    ".env.local"
    "components/dashboard/map-component.tsx"
    "components/dashboard/map-section.tsx"
    "components/dashboard/analytics-cards.tsx"
    "components/dashboard/route-comparison.tsx"
    "components/dashboard/input-card.tsx"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (MISSING)"
    fi
done

# Check 3: Backend running
echo ""
echo "✓ Checking backend..."
if curl -s http://localhost:5000/ > /dev/null 2>&1; then
    echo "  ✅ Flask backend running on :5000"
else
    echo "  ⚠️  Flask backend not detected"
    echo "     Start it with: python app.py"
fi

# Check 4: Package.json dependencies
echo ""
echo "✓ Checking dependencies in package.json..."
required_packages=(
    '"leaflet"'
    '"react-leaflet"'
    '"sonner"'
)

for pkg in "${required_packages[@]}"; do
    if grep -q "$pkg" package.json; then
        echo "  ✅ $pkg found"
    else
        echo "  ⚠️  $pkg not found (run npm install)"
    fi
done

# Check 5: Environment variables
echo ""
echo "✓ Checking environment configuration..."
if [ -f ".env.local" ]; then
    echo "  ✅ .env.local exists"
    if grep -q "NEXT_PUBLIC_API_URL" .env.local; then
        echo "  ✅ NEXT_PUBLIC_API_URL configured"
    else
        echo "  ⚠️  NEXT_PUBLIC_API_URL missing from .env.local"
    fi
else
    echo "  ⚠️  .env.local not found"
fi

echo ""
echo "=============================================="
echo "✅ Integration Verification Complete!"
echo ""
echo "Next steps:"
echo "1. npm install                    # Install dependencies"
echo "2. python app.py                  # Start Flask backend (new terminal)"
echo "3. npm run dev                    # Start Next.js frontend"
echo "4. Visit http://localhost:3000    # Open dashboard"
echo ""
