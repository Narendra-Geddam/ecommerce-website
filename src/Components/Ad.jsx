import React from 'react'
// import Link
import { Link } from 'react-router-dom'

function Ad() {
  return (
    <section className='bg-blue-200 h-[600px] py-24'>
        <div className='container mx-auto flex justify-around h-full'>
        {/* text */}
        <div className='flex flex-col justify-center'>
            <div className='font-semibold flex items-center uppercase'>
                <div className='w-10 h-[2px] bg-red-500 mr-3'></div>
                <div>New Trend</div>
            </div>
            <h1 className='text-[70px] leading-[1.1] font-light mb-4'>DJ SALE STYLISH <br />
            <span className='font-semibold'>MENS</span>
            </h1>
            <Link to={'/'} className='self-start uppercase font-semibold border-b-2 border-primary'>
                Discover More
            </Link>
        </div>
        </div>
    </section>
  )
}

export default Ad