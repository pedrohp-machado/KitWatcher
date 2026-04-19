import { useState, useEffect } from 'react'
import { getPriceHistory, getProducts } from '../services/api'
import ProductCard from '../components/ProductCard'
import PriceChart from '../components/PriceChart'

function Dashboard() {
    const [products, setProducts] = useState([])
    const [loading, setLoading] = useState(true)

    const [selected, setSelected] = useState(null)
    const [history, setHistory] = useState([])

    const [filter, setFilter] = useState('todos')

    const filtered = filter === 'todos'
        ? products
        : products.filter(p => p.store === filter)

    const handleSelectProduct = (product) => {
        setSelected(product)
        getPriceHistory(product.id)
            .then(response => setHistory(response.data))
            .catch(error => console.error('Erro ao buscar historico de precos: ', error))
    }

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

            {selected && (
                <div>
                    <h2>{selected.name} - {selected.store}</h2>
                    <PriceChart history={history} />
                </div>
            )}

            <div className="products-grid">
                {filtered.map(product => (
                    <ProductCard 
                        key={product.id} 
                        product={product}
                        onClick={() => handleSelectProduct(product)}
                    />
                ))}
            </div>
        </div>
    )
}

export default Dashboard