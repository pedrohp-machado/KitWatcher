import axios from 'axios'

const api = axios.create({
    baseURL: 'http://localhost:8000'
})

export const getPriceHistory = (productId) =>
    api.get(`/products/${productId}/price-history`)

export const getProducts = () => 
    api.get('/products')

export default api