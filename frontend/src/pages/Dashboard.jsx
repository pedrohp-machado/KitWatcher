import { useState, useEffect } from 'react'
import { getProducts } from '../services/api'
import ProductCard from '../components/ProductCard'

function Dashboard() {
    const [products, setProducts] = useState([])
    const [loading, setLoading] = useState(true)

    const [filter, setFilter] = useState('todos')

    const filtered = filter === 'todos'
        ? products
        : products.filter(p => p.store === filter)

    useEffect(() => {
        
        getProducts()
            .then(response => {
                setProducts(response.data)
                setLoading(false)
            })
            .catch(error => {
                console.error('Erro ao buscar produtos: ', error)
                setLoading(false)
            })
    }, [])

    if (loading) return <p>Carregando... </p>

    return (
        <div>
            <div className="filters">
                <button onClick={() => setFilter('todos')}>Todos</button>
                <button onClick={() => setFilter('netshoes')}>Netshoes</button>
                <button onClick={() => setFilter('futfanatics')}>FutFanatics</button>
            </div>

            <div className="products-grid">
                {filtered.map(product => (
                    <ProductCard key={product.id} product={product} />
                ))}
            </div>
        </div>
    )
}

export default Dashboard