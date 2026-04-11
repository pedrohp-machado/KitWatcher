import { useState, useEffect } from 'react'
import { getProducts } from '../services/api'
import ProductCard from '../components/ProductCard'

function Dashboard() {
    const [products, setProducts] = useState([])
    const [loading, setLoading] = useState(true)

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
            <h1>Monitor de camisas</h1>
            <div className="products-grid">
                {products.map(product => (
                    <ProductCard key={product.id} product={product} />
                ))}
            </div>
        </div>
    )
}

export default Dashboard