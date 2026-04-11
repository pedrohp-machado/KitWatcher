function ProductCard({ product }) {
    return (
        <div className="product-card">
            {!product.prices || product.prices.length === 0 ? null : (
                <>
                    <img src={product.image_url} alt={product.name}/>
                    <h3>{product.name}</h3>
                    <p>{product.store}</p>
                    <p> R$ {parseFloat(product.prices[0].price).toFixed(2)}</p>
                    {product.prices[0].discount > 0 && <span>-{product.prices[0].discount}% OFF</span>}
                </>
            )}
        </div>
    )
}

export default ProductCard