// FILE: ProductPage.jsx
import React, { useState, useEffect, useMemo, useCallback } from 'react';

// Memoized ProductCard component
const ProductCard = React.memo(({ product, onAddToCart }) => (
  <div className="product-card">
    <img src={product.image} alt={product.title} />
    <h3>{product.title}</h3>
    <p>${product.price}</p>
    <button onClick={() => onAddToCart(product)}>Add to Cart</button>
  </div>
));

// Memoized CartItem component
const CartItem = React.memo(({ item, onRemove }) => (
  <div className="cart-item">
    <span>{item.title} x {item.quantity}</span>
    <span>${(item.price * item.quantity).toFixed(2)}</span>
    <button onClick={() => onRemove(item.id)}>Remove</button>
  </div>
));

const ProductPage = () => {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [cart, setCart] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch products
  useEffect(() => {
    setIsLoading(true);
    fetch('https://fakestoreapi.com/products')
      .then(response => response.json())
      .then(data => {
        setProducts(data);
        setCategories([...new Set(data.map(p => p.category))]);
        setIsLoading(false);
      })
      .catch(err => {
        console.error(err);
        setError('Failed to load products');
        setIsLoading(false);
      });
  }, []);

  // Memoized filtered products
  const filteredProducts = useMemo(() => {
    return products.filter(p =>
      (!selectedCategory || p.category === selectedCategory) &&
      p.title.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [products, selectedCategory, searchTerm]);

  // Cart handlers
  const addToCart = useCallback((product) => {
    setCart(prevCart => {
      const exists = prevCart.find(item => item.id === product.id);
      if (exists) {
        return prevCart.map(item =>
          item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item
        );
      }
      return [...prevCart, { ...product, quantity: 1 }];
    });
  }, []);

  const removeFromCart = useCallback((id) => {
    setCart(prevCart => prevCart.filter(item => item.id !== id));
  }, []);

  const calculateTotal = useMemo(() => {
    return cart.reduce((total, item) => total + item.price * item.quantity, 0).toFixed(2);
  }, [cart]);

  return (
    <div className="product-page">
      <div className="filters">
        <input
          type="text"
          placeholder="Search products..."
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
        />
        <select value={selectedCategory} onChange={e => setSelectedCategory(e.target.value)}>
          <option value="">All Categories</option>
          {categories.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {isLoading && <p>Loading products...</p>}
      {error && <p className="error">{error}</p>}

      <div className="product-grid">
        {!isLoading && filteredProducts.map(product => (
          <ProductCard key={product.id} product={product} onAddToCart={addToCart} />
        ))}
      </div>

      <div className="cart">
        <h2>Shopping Cart</h2>
        {cart.length === 0 ? (
          <p>Your cart is empty</p>
        ) : (
          <>
            {cart.map(item => (
              <CartItem key={item.id} item={item} onRemove={removeFromCart} />
            ))}
            <div className="cart-total">
              <strong>Total: ${calculateTotal}</strong>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ProductPage;

// FILE: Dashboard.jsx
import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';

const fetchSalesData = async (startDate, endDate, category) => {
  const data = [
    { date: '2023-01-01', Electronics: 500, Clothing: 700, Food: 200 },
    { date: '2023-01-02', Electronics: 600, Clothing: 650, Food: 300 },
  ];
  return data;
};


const Dashboard = () => {
  const [salesData, setSalesData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [startDate, setStartDate] = useState('2023-01-01');
  const [endDate, setEndDate] = useState('2023-01-07');
  const [category, setCategory] = useState('');

  useEffect(() => {
    setLoading(true);
    fetchSalesData(startDate, endDate, category).then((data) => {
      setSalesData(data);
      setLoading(false);
    });
  }, [startDate, endDate, category]);

  const lineChartData = {
    labels: salesData.map(item => item.date),
    datasets: [
      { label: 'Electronics', data: salesData.map(item => item.Electronics), borderColor: 'blue' },
      { label: 'Clothing', data: salesData.map(item => item.Clothing), borderColor: 'green' },
      { label: 'Food', data: salesData.map(item => item.Food), borderColor: 'red' },
    ],
  };

  return (
    <div>
      <h1>Sales Dashboard</h1>
      
      <div>
        <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
        <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
        <select onChange={(e) => setCategory(e.target.value)} value={category}>
          <option value="">All Categories</option>
          <option value="Electronics">Electronics</option>
          <option value="Clothing">Clothing</option>
          <option value="Food">Food</option>
        </select>
      </div>

      {loading ? <p>Loading...</p> : <Line data={lineChartData} />}
    </div>
  );
};

export default Dashboard;

// FILE: Dashboard.css
.dashboard-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.filters-container {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 20px;
}

.chart-container {
  height: 400px;
  margin-bottom: 30px;
  border: 1px solid #ddd;
  border-radius: 5px;
  padding: 15px;
  background-color: #fff;
  width: 100%;
  box-sizing: border-box;
}

.table-container {
  margin-bottom: 30px;
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 600px; 
}

.data-table th,
.data-table td {
  padding: 10px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.data-table th {
  background-color: #f5f5f5;
}

.summary-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.summary-card {
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 5px;
  padding: 15px;
  box-sizing: border-box;
}

.summary-card h3 {
  margin-top: 0;
  margin-bottom: 10px;
  color: #333;
}

.summary-card p {
  font-size: 20px;
  font-weight: bold;
  margin: 0;
}

.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.error {
  color: red;
  padding: 20px;
  background-color: #ffebee;
  border-radius: 5px;
  margin-bottom: 20px;
  box-sizing: border-box;
}

@media (max-width: 768px) {
  .filters-container {
    flex-direction: column;
  }

  .chart-container {
    height: auto;
  }

  .data-table {
    font-size: 14px;
  }

  .summary-card p {
    font-size: 18px;
  }
}

@media (max-width: 480px) {
  .data-table th,
  .data-table td {
    padding: 8px;
  }

  .summary-card p {
    font-size: 16px;
  }
}


// FILE: optimization-review.md
# Performance Optimization Review

## Identified Optimization Opportunities

1. **Issue:** Avoid Duplicate State for Filtered Products
  - **Description:** Right now, the filteredProducts state is duplicating data that can be derived from products, searchTerm, and selectedCategory.

  - **Proposed Solution:** Instead of storing filteredProducts, we can use useMemo to compute the filtered list directly from the other states.

  - **Benefits:** This will save memory and prevent inconsistencies between products and filteredProducts. It also makes the code cleaner.

2.  **Issue:** Memoize Render Functions (renderProducts, renderCartItems)
  - **Description:** The renderProducts and renderCartItems functions are created again every time the component renders.

  - **Proposed Solution:** We can memoize these functions using useCallback or even move them outside the component body if they don’t rely on local state. useMemo could also be used to cache their results.

  - **Benefits:** Memoization helps make sure we’re not re-creating the same functions every time the component updates. This can speed things up, especially when we're working with big lists or tasks that take more time to process.

3. **Issue:** Refactor Cart Logic for Better Performance
  - **Description:** The cart-related functions (addToCart, removeFromCart, calculateTotal) are currently mixed in with the component's rendering code, which makes things harder to manage.

  - **Proposed Solution:** Moving the cart logic into a custom hook (like useCart) or using useReducer for managing cart state would make it more efficient and easier to handle.

  - **Benifits:** This separation of concerns not only makes the component cleaner and easier to maintain but also optimizes state updates, making them more efficient and easier to manage in the long run.

4. **Issue:** Break Up the Code Into Smaller Components
  - **Description:** Right now, the JSX for rendering products and cart items is a bit repetitive and not very modular.

  - **Proposed Solution:** We can extract ProductCard and CartItem as separate components, and use React.memo to avoid unnecessary re-renders.

  - **Benefits:** This improves the reusability of the components, reduces code duplication, and ensures that these components only re-render when necessary, which boosts performance.

5. **Issue:** Separate Error Handling from UI Logic
  - **Description:** Error logging and UI state updates are happening in the same .catch block.

  - **Proposed Solution:** It’s better to separate the error logging from the UI. We can create a centralized error handler or use a logging service.

  - **Benefits:** Keeping logging separate from the UI helps the app run more smoothly and avoids slowdowns. It also makes handling errors cleaner and easier to organize.

