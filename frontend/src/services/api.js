import axios from 'axios'

const api = axios.create({
    baseURL: 'http://localhost:8000'
})

export const getProducts = () => api.get('/products')

export default api