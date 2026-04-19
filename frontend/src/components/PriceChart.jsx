import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

function PriceChart({ history }) {

    const data = history.map(h => ({
        date: new Date (h.collected_at).toLocaleDateString('pt-BR'),
        price: parseFloat(h.price)
    }))

    return (
        <div className="price-chart">

            <h3>Historico de Precos</h3>
            <ResponsiveContainer width="100%" height={300}>

                <LineChart data={data}>
                
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip formatter={(value) => `R$ ${value.toFixed(2)}`} />
                    <Line type="monotone" dataKey="price" stroke="#8884d8" />    
                
                </LineChart>
            
            </ResponsiveContainer>

        </div>
    )

}

export default PriceChart